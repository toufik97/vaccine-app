import json
from datetime import datetime, timedelta
from core.enums import VaccineStatus, PneumoProtocol

class Scheduler:
    def __init__(self, api):
        self.api = api
        self.milestones = []
        self.rules = {}
        self.load_protocols()

    def load_protocols(self):
        data = self.api.get_vaccine_families_with_doses()
        
        if data and "milestones_order" in data:
            # Rebuild the old self.milestones format: [(name, target_days, [vaccines...]), ...]
            milestones_order = data.get("milestones_order", [])
            vaccines = data.get("vaccines", [])

            self.milestones = []
            self.rules = {}
            self.catchup_profiles = data.get("catchup_profiles", [])

            # First, group doses by milestone
            milestone_dict = {}
            for m in milestones_order:
                milestone_dict[m["name"]] = {
                    "target_days": m["target_days"],
                    "doses": []
                }

            # Map vaccines into rules and milestones
            for vax in vaccines:
                for dose in vax.get("doses", []):
                    dose_id = dose["id"]
                    m_name = dose["milestone"]
                    dose_rules = dose.get("rules", {})

                    # Extract rules identically to the old format
                    self.rules[dose_id] = dose_rules

                    # Add dose to the milestone array
                    if m_name in milestone_dict:
                        milestone_dict[m_name]["doses"].append(dose_id)

            # Build the final self.milestones array in the correct order
            for m in milestones_order:
                name = m["name"]
                target = m["target_days"]
                self.milestones.append((name, target, milestone_dict[name]["doses"]))

        else:
            self.milestones = []
            self.rules = {}
            self.catchup_profiles = []

    def get_next_available_date(self, base_date_obj, vax_name, center_schedule):
        allowed_days = center_schedule.get(vax_name, center_schedule.get("default", [0, 1, 2, 3, 4]))
        current_date = base_date_obj
        while current_date.weekday() not in allowed_days:
            current_date += timedelta(days=1)
        return current_date

    def get_vaccine_rules(self, vax_name):
        rule_set = self.rules.get(vax_name, {})
        # Check if rules are still nested under "Old" or "New" after transition
        if "Old" in rule_set or "New" in rule_set:
            # We fallback to "New" rules if old/new structured as a preference 
            # (although api_client merged them, it might be nested)
            return rule_set.get("New", rule_set.get("Old", {}))
        return rule_set

    def generate_expected_vaxes(self, dob_str, no_proof=False):
        dob_obj = datetime.strptime(dob_str, "%Y-%m-%d")
        age_days = (datetime.now() - dob_obj).days
        age_months = age_days / 30.44

        expected_vaxes = []
        for milestone, target, vaxes in self.milestones:
            for vax in vaxes:
                if vax == "Pneumo3_NewOnly": # Legacy removal protection
                    continue
                expected_vaxes.append({"milestone": milestone, "vaccine": vax})

        if not no_proof:
            return [(v["milestone"], v["vaccine"]) for v in expected_vaxes]

        active_profile = None
        for profile in getattr(self, "catchup_profiles", []):
            min_days = profile.get("min_age_days", 0)
            max_days = profile.get("max_age_days", 99999)
            if min_days <= age_days <= max_days:
                active_profile = profile
                break
                
        if active_profile:
            rules = active_profile.get("rules", {})
            
            # 1. DTC_Ag Family Processing (Penta -> DTC -> Td transition)
            if "DTC_Ag" in rules:
                dtc_rule = rules["DTC_Ag"]
                target_doses = dtc_rule.get("doses", 3)
                variants = dtc_rule.get("variants", [])
                
                # Filter out all default DTC/Penta/Td scheduled vaccines
                expected_vaxes = [v for v in expected_vaxes if not (
                    v["vaccine"].startswith("Penta") or 
                    v["vaccine"].startswith("DTC") or 
                    v["vaccine"].startswith("Td")
                )]
                # Track occurrences of each variant to accurately name them (e.g., Penta1, Penta2, DTC1)
                variant_counts = {}
                
                # Inject custom doses based on the profile
                for i in range(target_doses):
                    # Pick the variant type from the array based on dose number, or default to the last one if array is shorter
                    variant_type = variants[i] if i < len(variants) else variants[-1]
                    
                    variant_counts[variant_type] = variant_counts.get(variant_type, 0) + 1
                    count = variant_counts[variant_type]
                    
                    # We inject them all sequentially into the first milestones
                    ms_name = self.milestones[min(i, len(self.milestones)-1)][0]
                    
                    # Name formulation: Add the count if it's expected to have multiple doses in the DB history
                    vax_name = f"{variant_type}{count}"
                    if variant_type == "Td": vax_name = f"Td{count}" # Ensure Td gets a counter
                    
                    expected_vaxes.insert(i, {"milestone": ms_name, "vaccine": vax_name})

            # 2. Polio_Ag Family Processing (4 vs 5 doses depending on age & 1st dose VPI injection)
            if "Polio_Ag" in rules:
                polio_rule = rules["Polio_Ag"]
                min_vpo = polio_rule.get("min_vpo", 4)
                
                current_vpo = [v for v in expected_vaxes if v["vaccine"].startswith("VPO")]
                
                # If the schedule currently projects more VPOs than the catchup requires (e.g. they missed 5 years worth), we cap it. 
                # (But usually the schedule already projects 5 total).
                if len(current_vpo) > min_vpo:
                   excess = len(current_vpo) - min_vpo
                   for _ in range(excess):
                       # Remove the last VPOs
                       last_vpo = [v for v in expected_vaxes if v["vaccine"].startswith("VPO")][-1]
                       expected_vaxes.remove(last_vpo)
                       
                # RULE: If no proof AT ALL, the first VPO dose must be accompanied by a VPI (CPI)
                has_cpi = any(v["vaccine"].startswith("CPI") for v in expected_vaxes if isinstance(v, dict) and "vaccine" in v)
                if not has_cpi and min_vpo > 0:
                    first_vpo_ms = current_vpo[0]["milestone"] if current_vpo else self.milestones[0][0]
                    # Insert CPI1 alongside the first VPO
                    expected_vaxes.insert(0, {"milestone": first_vpo_ms, "vaccine": "CPI1"})
                    
            # 3. PCV Age Caps (e.g., 2 doses if between 1-3 years old)
            if "PCV" in rules:
                pcv_rule = rules["PCV"]
                cap = pcv_rule.get("cap", 4)
                
                current_pcvs = [v for v in expected_vaxes if v["vaccine"].startswith("PCV")]
                if len(current_pcvs) > cap:
                    excess = len(current_pcvs) - cap
                    for _ in range(excess):
                        last_pcv = [v for v in expected_vaxes if v["vaccine"].startswith("PCV")][-1]
                        expected_vaxes.remove(last_pcv)

        return [(v["milestone"], v["vaccine"]) for v in expected_vaxes]

    def calculate_updates(self, dob_str, records_dict, center_schedule):
        """
        records_dict should be a dict mapped by vax_name: {"status": ..., "date_given": ..., "due_date": ...}
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
                # If "Pneumo3_NewOnly" is in milestone, we skip it (legacy)
                if vax == "Pneumo3_NewOnly":
                    continue
                    
                rules = self.get_vaccine_rules(vax)
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
                            
                # Dynamic generic conflicts (e.g., Penta vs PCV)
                for conflict in rules.get("conflicts", []):
                    conflict_vaxes = conflict.get("vaccines", [])
                    min_interval = conflict.get("min_interval_days", 0)
                    for cv in conflict_vaxes:
                        if cv in projected_dates:
                            conflict_min_date = projected_dates[cv] + timedelta(days=min_interval)
                            if conflict_min_date > min_valid_date:
                                min_valid_date = conflict_min_date

                # Dynamic Live vaccine conflicts (28-day rule unless same day)
                if rules.get("is_live", False) and not rules.get("live_conflict_exception", False):
                    for prev_vax, prev_date in projected_dates.items():
                        if prev_vax in vaccines:
                            continue # Same milestone usually means same day, no 28-day penalty
                        prev_rules = self.get_vaccine_rules(prev_vax)
                        if prev_rules and prev_rules.get("is_live", False) and not prev_rules.get("live_conflict_exception", False):
                            live_min_date = prev_date + timedelta(days=28)
                            if live_min_date > min_valid_date:
                                min_valid_date = live_min_date
                            
                # Schedule at the target milestone date, unless medical rules push it further
                valid_dates_for_milestone[vax] = max(target_date, min_valid_date)
                
            if not valid_dates_for_milestone:
                continue

            # Check 14-day grouping strictly for core milestone vaccines (exclude offset vaccines)
            core_vaccines = [v for v in valid_dates_for_milestone.keys() if not self.get_vaccine_rules(v).get("offset_from_milestone_days")]
            
            if core_vaccines:
                min_core_date = min([valid_dates_for_milestone[v] for v in core_vaccines])
                max_core_date = max([valid_dates_for_milestone[v] for v in core_vaccines])
                
                if (max_core_date - min_core_date).days <= 14:
                    # Group them!
                    for v in core_vaccines:
                        valid_dates_for_milestone[v] = max_core_date

            # Apply offset for offset vaccines (e.g., Pneumo New protocol)
            for vax, date_val in valid_dates_for_milestone.items():
                rules = self.get_vaccine_rules(vax)
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

    def get_core_vaccines(self, milestone_name):
        """
        Returns a list of vaccine names for a given milestone that DO NOT have an offset rule.
        Also accurately excludes logic-skipped vaccines like Pneumo3_NewOnly.
        """
        core_vaccines = []
        for m_name, _, vaccines in self.milestones:
            if m_name == milestone_name:
                for vax in vaccines:
                    if vax == "Pneumo3_NewOnly":
                        continue
                    
                    rules = self.get_vaccine_rules(vax)
                    if rules and rules.get("offset_from_milestone_days"):
                        continue
                    core_vaccines.append(vax)
                break
        return core_vaccines

    def get_independent_vaccines(self):
        """
        Returns a list of vaccines that do NOT have any "dependencies" declared in their rules.
        """
        independent_vaxes = []
        for m_name, _, vaccines in self.milestones:
            for vax in vaccines:
                if vax == "Pneumo3_NewOnly":
                    continue
                
                rules = self.get_vaccine_rules(vax)
                
                # A vaccine is independent if it has no dependencies array (or it is empty)
                if not rules or not rules.get("dependencies"):
                    independent_vaxes.append(vax)
                    
        return independent_vaxes

    def validate_vaccine_input(self, dob_str, records_dict, vax_name, input_date=None):
            
        dob_obj = datetime.strptime(dob_str, "%Y-%m-%d").date()
        rules = self.get_vaccine_rules(vax_name)
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
                    
        for conflict in rules.get("conflicts", []):
            conflict_vaxes = conflict.get("vaccines", [])
            min_interval = conflict.get("min_interval_days", 0)
            for cv in conflict_vaxes:
                if cv in records_dict:
                    rec = records_dict[cv]
                    if rec["status"] in [VaccineStatus.DONE.value, VaccineStatus.EXTERNE.value] and rec["date_given"]:
                        if rec["date_given"] != "Inconnue":
                            cv_date = datetime.strptime(rec["date_given"], "%Y-%m-%d").date()
                            if input_date < cv_date + timedelta(days=min_interval):
                                return f"Intervalle minimum de {min_interval} jours avec {cv} non respecté (Conflit PNI)."

        if rules.get("is_live", False) and not rules.get("live_conflict_exception", False):
            for prev_vax, prev_rec in records_dict.items():
                if prev_vax == vax_name: continue
                if prev_rec["status"] in [VaccineStatus.DONE.value, VaccineStatus.EXTERNE.value] and prev_rec["date_given"]:
                    if prev_rec["date_given"] != "Inconnue":
                        prev_date = datetime.strptime(prev_rec["date_given"], "%Y-%m-%d").date()
                        if prev_date != input_date and abs((input_date - prev_date).days) < 28:
                            prev_rules = self.get_vaccine_rules(prev_vax)
                            if prev_rules and prev_rules.get("is_live", False) and not prev_rules.get("live_conflict_exception", False):
                                return f"Intervalle minimum de 28 jours avec l'autre vaccin vivant ({prev_vax}) non respecté."
                                
        # --- NEW CONFLICT: Same Date / Same Site Check ---
        input_site = rules.get("default_injection_site")
        
        # Don't throw errors for things without sites, or Oral routes which can be given easily together
        if input_site and rules.get("administration_route") != "Oral" and input_site != "Oral":
            for prev_vax, prev_rec in records_dict.items():
                if prev_vax == vax_name: continue
                # We only care about vaccines given on the EXACT same day we are trying to schedule now
                if prev_rec["status"] in [VaccineStatus.DONE.value, VaccineStatus.EXTERNE.value] and prev_rec["date_given"]:
                    if prev_rec["date_given"] != "Inconnue":
                        prev_date = datetime.strptime(prev_rec["date_given"], "%Y-%m-%d").date()
                        if prev_date == input_date:
                            prev_rules = self.get_vaccine_rules(prev_vax)
                            if prev_rules and prev_rules.get("default_injection_site") == input_site:
                                return f"Conflit de site d'injection: {prev_vax} est déjà programmé pour le même site ({input_site}) aujourd'hui."
        # -------------------------------------------------

        offset_days = rules.get("offset_from_milestone_days")
        if offset_days:
            milestone_name = None
            for m_name, _, m_vaxes in self.milestones:
                if vax_name in m_vaxes:
                    milestone_name = m_name
                    break
            
            if milestone_name:
                core_vaxes = self.get_core_vaccines(milestone_name)
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
