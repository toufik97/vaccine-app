import requests
import json

class ApiClient:
    def __init__(self, base_url="http://127.0.0.1:8000/api/"):
        self.base_url = base_url

    def _get(self, endpoint):
        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error [GET {endpoint}]: {e}")
            return None

    def _post(self, endpoint, data):
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error [POST {endpoint}]: {e}\nResponse: {getattr(e.response, 'text', '')}")
            raise e

    def _put(self, endpoint, data):
        try:
            response = requests.put(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error [PUT {endpoint}]: {e}\nResponse: {getattr(e.response, 'text', '')}")
            raise e

    def _delete(self, endpoint):
        try:
            response = requests.delete(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"API Error [DELETE {endpoint}]: {e}\nResponse: {getattr(e.response, 'text', '')}")
            return False

    # --- SETTINGS ---
    def get_settings(self):
        """Fetches settings and packs them into a single config dict"""
        data = self._get("settings/")
        if data is None: return None
        
        config = {}
        for item in data:
            key = item['key']
            val_str = item['value']
            try:
                config[key] = json.loads(val_str)
            except:
                config[key] = val_str
        return config

    def save_settings(self, config_dict):
        """Overwrites or updates settings sequentially"""
        for key, value in config_dict.items():
            val_str = json.dumps(value) if isinstance(value, (dict, list, bool, int, float)) else str(value)
            # Try to PUT, if 404, then POST
            endpoint = f"settings/{key}/"
            try:
                self._put(endpoint, {"key": key, "value": val_str})
            except requests.RequestException as e:
                if e.response and e.response.status_code == 404:
                    self._post("settings/", {"key": key, "value": val_str})
                else:
                    raise e
        return True

    # --- PROTOCOLS ---
    def get_vaccine_families_with_doses(self):
        """Fetches the nested rules built identically to protocols.json layout"""
        milestones_data = self._get("milestones/")
        families_data = self._get("vaccine-families/")
        
        if milestones_data is None or families_data is None:
            return None

        milestones_order = [{"name": m["name"], "target_days": m["target_days"]} for m in sorted(milestones_data, key=lambda x: x["order_index"])]
        
        vaccines = []
        for family in families_data:
            f_dict = {
                "id": family["id_name"],
                "name": family["display_name"],
                "description": family["description"],
                "doses": []
            }
            
            # Reconstruct legacy dose dictionaries
            doses = []
            for d in family.get("doses", []):
                rules = {}
                min_age = d.get("min_age_days", 0)
                offset = d.get("offset_days", 0)
                if min_age > 0: rules["min_age_days"] = min_age
                if offset > 0: rules["offset_from_milestone_days"] = offset
                adv = d.get("advanced_rules", {})
                if adv: rules.update(adv)
                
                base_id = d["id"]
                if base_id.endswith("_Old"): base_id = base_id[:-4]
                elif base_id.endswith("_New"): base_id = base_id[:-4]
                
                dose_dict = {"id": base_id, "milestone": d["milestone_name"]}
                proto = d.get("pneumo_protocol", "All")
                
                if proto in ["Old", "New"]:
                    dose_dict["rules"] = {proto: rules}
                else:
                    dose_dict["rules"] = rules
                doses.append(dose_dict)
                
            # Merge dual-protocol rows into a single dictionary entry for the UI
            merged_doses = {}
            for d in doses:
                d_id = d["id"]
                if d_id not in merged_doses:
                    merged_doses[d_id] = d
                else:
                    if "Old" in d["rules"] or "New" in d["rules"]:
                        merged_doses[d_id]["rules"].update(d["rules"])
            
            f_dict["doses"] = list(merged_doses.values())
            vaccines.append(f_dict)
            
        return {
            "milestones_order": milestones_order,
            "vaccines": vaccines
        }

    def save_protocols_to_api(self, data):
        """Pushes the entire protocols definition to the Django bulk-upload endpoint"""
        try:
            self._post("upload-protocols/", data)
            return True
        except requests.RequestException as e:
            print(f"Failed to upload protocols: {e}")
            raise e
