import json
import os
from datetime import datetime, timedelta
from core.enums import VaccineStatus, PneumoProtocol

class Scheduler:
    def __init__(self):
        self.milestones = []
        self.rules = {}
        self.load_protocols()

    def load_protocols(self):
        protocol_file = 'protocols.json'
        if os.path.exists(protocol_file):
            with open(protocol_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.milestones = [(m[0], m[1], m[2]) for m in data.get("milestones", [])]
                self.rules = data.get("rules", {})
        else:
            self.milestones = []
            self.rules = {}

    def get_next_available_date(self, base_date_obj, vax_name, center_schedule):
        allowed_days = center_schedule.get(vax_name, center_schedule.get("default", [0, 1, 2, 3, 4]))
        current_date = base_date_obj
        while current_date.weekday() not in allowed_days:
            current_date += timedelta(days=1)
        return current_date

    def get_vaccine_rules(self, vax_name, pneumo_mode):
        rule_set = self.rules.get(vax_name, {})
        # Dynamic handling for Pneumo versions
        if "Old" in rule_set or "New" in rule_set:
            return rule_set.get(pneumo_mode, {})
        return rule_set

    def calculate_updates(self, dob_str, records_dict, center_schedule, pneumo_mode=PneumoProtocol.OLD.value):
        """
        records_dict should be a dict mapped by vax_name: {"status": ..., "date_given": ..., "due_date": ...}
        pneumo_mode can be "Old" (3 doses) or "New" (4 doses)
        Returns a list of tuples: (new_due_str, vax_name)
        """
        dob_obj = datetime.strptime(dob_str, "%Y-%m-%d")
        updates = []
        projected_dates = {}

        for milestone_name, target_days, vaccines in self.milestones:
            target_date = dob_obj + timedelta(days=target_days)
            # We first calculate the individual medically allowed minimum dates for each vaccine.
            valid_dates_for_milestone = {}
            for vax in vaccines:
                # If "Pneumo3_NewOnly" is in milestone but pneumo_mode is Old, we skip it
                if vax == "Pneumo3_NewOnly" and pneumo_mode == PneumoProtocol.OLD.value:
                    continue
                    
                rules = self.get_vaccine_rules(vax, pneumo_mode)
                if not rules:
                    # Fallback logic if no rules are defined for a vaccine
                    valid_dates_for_milestone[vax] = target_date
                    continue
                    
                min_valid_date = dob_obj + timedelta(days=rules.get("min_age_days", 0))

                for dep in rules.get("dependencies", []):
                    dep_vax = dep["vaccine"]
                    min_interval = dep["min_interval_days"]
                    if dep_vax in projected_dates:
                        dep_date = projected_dates[dep_vax]
                        dep_min_date = dep_date + timedelta(days=min_interval)
                        if dep_min_date > min_valid_date:
                            min_valid_date = dep_min_date
                            
                # Schedule at the target milestone date, unless medical rules push it further
                valid_dates_for_milestone[vax] = max(target_date, min_valid_date)
                
            if not valid_dates_for_milestone:
                continue

            # Check 14-day grouping strictly for core milestone vaccines (exclude offset vaccines)
            core_vaccines = [v for v in valid_dates_for_milestone.keys() if not self.get_vaccine_rules(v, pneumo_mode).get("offset_from_milestone_days")]
            
            if core_vaccines:
                min_core_date = min([valid_dates_for_milestone[v] for v in core_vaccines])
                max_core_date = max([valid_dates_for_milestone[v] for v in core_vaccines])
                
                if (max_core_date - min_core_date).days <= 14:
                    # Group them!
                    for v in core_vaccines:
                        valid_dates_for_milestone[v] = max_core_date

            # Apply offset for offset vaccines (e.g., Pneumo New protocol)
            for vax, date_val in valid_dates_for_milestone.items():
                rules = self.get_vaccine_rules(vax, pneumo_mode)
                offset = rules.get("offset_from_milestone_days")
                
                if offset and core_vaccines:
                    ref_vaxes = rules.get("offset_reference_vaccines", core_vaccines)
                    # Check for Rupture exception
                    is_rupture_exception = False
                    if rules.get("rupture_fallback_offset"):
                        for cv in ref_vaxes:
                            if cv in records_dict and records_dict[cv]["status"] == VaccineStatus.RUPTURE.value:
                                is_rupture_exception = True
                                break
                                
                    if not is_rupture_exception:
                        max_core_date = None
                        for cv in ref_vaxes:
                            if cv in records_dict and records_dict[cv]["status"] in [VaccineStatus.DONE.value, VaccineStatus.EXTERNE.value] and records_dict[cv]["date_given"] and records_dict[cv]["date_given"] != "Inconnue":
                                cv_date = datetime.strptime(records_dict[cv]["date_given"], "%Y-%m-%d")
                            else:
                                cv_date = valid_dates_for_milestone.get(cv, target_date)
                                
                            if not max_core_date or cv_date > max_core_date:
                                max_core_date = cv_date
                                
                        if max_core_date and date_val < max_core_date + timedelta(days=offset):
                            valid_dates_for_milestone[vax] = max_core_date + timedelta(days=offset)

            # Map the accepted valid dates to final scheduled dates via center availability
            for vax, base_date in valid_dates_for_milestone.items():
                if vax not in records_dict:
                    continue
                record = records_dict[vax]
                
                if record["status"] in [VaccineStatus.DONE.value, VaccineStatus.EXTERNE.value] and record["date_given"]:
                    if record["date_given"] != "Inconnue":
                        projected_dates[vax] = datetime.strptime(record["date_given"], "%Y-%m-%d")
                    else:
                        projected_dates[vax] = base_date
                    continue
                
                final_date = self.get_next_available_date(base_date, vax, center_schedule)
                projected_dates[vax] = final_date
                
                if final_date.strftime("%Y-%m-%d") != record["due_date"]:
                    updates.append((final_date.strftime("%Y-%m-%d"), vax))
                    
        return updates

    def get_core_vaccines(self, milestone_name, pneumo_mode=PneumoProtocol.OLD.value):
        """
        Returns a list of vaccine names for a given milestone that DO NOT have an offset rule.
        Also accurately excludes logic-skipped vaccines like Pneumo3_NewOnly in Old mode.
        """
        core_vaccines = []
        for m_name, _, vaccines in self.milestones:
            if m_name == milestone_name:
                for vax in vaccines:
                    if vax == "Pneumo3_NewOnly" and pneumo_mode == PneumoProtocol.OLD.value:
                        continue
                    
                    rules = self.get_vaccine_rules(vax, pneumo_mode)
                    if rules and rules.get("offset_from_milestone_days"):
                        continue
                    core_vaccines.append(vax)
                break
        return core_vaccines

    def get_independent_vaccines(self, pneumo_mode=PneumoProtocol.OLD.value):
        """
        Returns a list of vaccines that do NOT have any "dependencies" declared in their rules.
        """
        independent_vaxes = []
        for m_name, _, vaccines in self.milestones:
            for vax in vaccines:
                if vax == "Pneumo3_NewOnly" and pneumo_mode == PneumoProtocol.OLD.value:
                    continue
                
                rules = self.get_vaccine_rules(vax, pneumo_mode)
                
                # A vaccine is independent if it has no dependencies array (or it is empty)
                if not rules or not rules.get("dependencies"):
                    independent_vaxes.append(vax)
                    
        return independent_vaxes

    def validate_vaccine_input(self, dob_str, records_dict, vax_name, pneumo_mode, input_date):
        dob_obj = datetime.strptime(dob_str, "%Y-%m-%d").date()
        rules = self.get_vaccine_rules(vax_name, pneumo_mode)
        if not rules: return None
            
        min_age_days = rules.get("min_age_days", 0)
        if input_date < dob_obj + timedelta(days=min_age_days):
            return f"Âge minimum non respecté ({min_age_days} jours requis)."
            
        for dep in rules.get("dependencies", []):
            dep_vax = dep["vaccine"]
            min_interval = dep["min_interval_days"]
            
            if dep_vax in records_dict:
                rec = records_dict[dep_vax]
                if rec["status"] in [VaccineStatus.DONE.value, VaccineStatus.EXTERNE.value] and rec["date_given"]:
                    if rec["date_given"] != "Inconnue":
                        dep_date = datetime.strptime(rec["date_given"], "%Y-%m-%d").date()
                        if input_date < dep_date + timedelta(days=min_interval):
                            return f"Intervalle minimum de {min_interval} jours avec {dep_vax} non respecté."
                else:
                    return f"Le vaccin précédent ({dep_vax}) n'a pas encore été administré."
                    
        offset_days = rules.get("offset_from_milestone_days")
        if offset_days:
            milestone_name = None
            for m_name, _, m_vaxes in self.milestones:
                if vax_name in m_vaxes:
                    milestone_name = m_name
                    break
            
            if milestone_name:
                core_vaxes = self.get_core_vaccines(milestone_name, pneumo_mode)
                ref_vaxes = rules.get("offset_reference_vaccines", core_vaxes)
                max_core_given = None
                is_rupture_exception = False
                
                if rules.get("rupture_fallback_offset"):
                    for cv in ref_vaxes:
                        if cv in records_dict and records_dict[cv]["status"] == VaccineStatus.RUPTURE.value:
                            is_rupture_exception = True
                            break

                if not is_rupture_exception:
                    for cv in ref_vaxes:
                        if cv in records_dict:
                            rec = records_dict[cv]
                            if rec["status"] in [VaccineStatus.DONE.value, VaccineStatus.EXTERNE.value] and rec["date_given"]:
                                if rec["date_given"] != "Inconnue":
                                    cv_date = datetime.strptime(rec["date_given"], "%Y-%m-%d").date()
                                    if not max_core_given or cv_date > max_core_given:
                                        max_core_given = cv_date
                            else:
                                return f"Les vaccins principaux ({cv}) du groupe {milestone_name} doivent être administrés en premier."
                        else:
                            return f"Les vaccins principaux ({cv}) du groupe {milestone_name} doivent être administrés en premier."
                    
                    if max_core_given and input_date < max_core_given + timedelta(days=offset_days):
                        return f"Décalage minimum de {offset_days} jours après les vaccins principaux (ex: {max_core_given.strftime('%d/%m/%Y')}) non respecté."
                else:
                    fallback_days = rules.get("fallback_min_interval_days")
                    if fallback_days and input_date < dob_obj + timedelta(days=fallback_days):
                        return f"L'âge minimum sans vaccins principaux est de {fallback_days} jours."
                    
        return None
