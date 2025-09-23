import json
from pathlib import Path
from datetime import datetime
from .api_client import APIClient


class DataManager:
    DATA_DIR = Path(__file__).parent.parent / "data"
    MAP_JSON = DATA_DIR / "cities.json"
    JOBS_JSON = DATA_DIR / "jobs.json"
    WEATHER_JSON = DATA_DIR / "weather.json"

    def __init__(self):
        self.api_client = APIClient()

    def _compare_versions(self, version1: str, version2: str) -> int:
        def version_to_tuple(v):
            try:
                return tuple(map(int, v.split('.')))
            except (ValueError, AttributeError):
                return (0, 0)

        v1_tuple = version_to_tuple(version1)
        v2_tuple = version_to_tuple(version2)

        max_len = max(len(v1_tuple), len(v2_tuple))
        v1_tuple = v1_tuple + (0,) * (max_len - len(v1_tuple))
        v2_tuple = v2_tuple + (0,) * (max_len - len(v2_tuple))

        if v1_tuple > v2_tuple:
            return 1
        elif v1_tuple < v2_tuple:
            return -1
        else:
            return 0

    def _add_version_to_json(self, api_data: dict, json_file_path: Path, data_type: str):
        try:
            # Load existing file or create new structure
            if json_file_path.exists() and json_file_path.stat().st_size > 0:
                try:
                    with open(json_file_path, "r", encoding="utf-8") as f:
                        file_data = json.load(f)
                except json.JSONDecodeError:
                    # Si el archivo está corrupto, crear nueva estructura
                    file_data = {"versions": []}
            else:
                file_data = {"versions": []}

            api_version = api_data.get("data", {}).get("version", "1.0")

            # Check if this version already exists
            version_exists = False
            for existing_version in file_data.get("versions", []):
                if existing_version.get("api_version") == api_version:
                    version_exists = True
                    print(
                        f"{data_type.capitalize()} version {api_version} already exists")
                    break

            # Add new version if it doesn't exist
            if not version_exists:
                new_version_entry = {
                    "entry_id": len(file_data.get("versions", [])) + 1,
                    "api_version": api_version,
                    "data": api_data.get("data"),
                    "added_at": datetime.now().isoformat()
                }

                if "versions" not in file_data:
                    file_data["versions"] = []

                file_data["versions"].append(new_version_entry)

                # Sort versions (newest first)
                file_data["versions"].sort(
                    key=lambda x: tuple(map(int, x["api_version"].split('.'))),
                    reverse=True
                )

                # Save updated file
                with open(json_file_path, "w", encoding="utf-8") as f:
                    json.dump(file_data, f, indent=4, ensure_ascii=False)

                print(
                    f"New {data_type} version {api_version} added successfully")
                return True

            return False

        except Exception as e:
            print(f"Error adding {data_type} version: {e}")
            return False

    def save_map_data(self):
        """Get map data from API and add new versions to JSON"""
        try:
            response = self.api_client.get_map_data()
            if response is not None:
                api_data = response.json()
                return self._add_version_to_json(api_data, self.MAP_JSON, "map")
        except Exception as e:
            print(f"Error fetching map data from API: {e}")
        return False

    def save_jobs_data(self):
        """Get jobs data from API and add new versions to JSON"""
        try:
            response = self.api_client.get_jobs_data()
            if response is not None:
                api_data = response.json()

                # Handle jobs structure: {"version": "1.0", "data": [...]}
                # where data is an array, not an object with version
                if isinstance(api_data, dict) and "data" in api_data and "version" in api_data:
                    # Wrap the structure to match expected format for _add_version_to_json
                    wrapped_data = {
                        "data": {
                            "version": api_data.get("version", "1.0"),
                            "jobs": api_data.get("data", [])
                        }
                    }
                    return self._add_version_to_json(wrapped_data, self.JOBS_JSON, "jobs")
                else:
                    # If API returns different structure, handle as before
                    return self._add_version_to_json(api_data, self.JOBS_JSON, "jobs")
        except Exception as e:
            print(f"Error fetching jobs data from API: {e}")
        return False

    def save_weather_data(self):
        """Get weather data from API and add new versions to JSON"""
        try:
            response = self.api_client.get_weather_data()
            if response is not None:
                api_data = response.json()
                return self._add_version_to_json(api_data, self.WEATHER_JSON, "weather")
        except Exception as e:
            print(f"Error fetching weather data from API: {e}")

    def load_map(self):
        try:  # Try to get map data from API
            response = self.api_client.get_map_data()
            if response is not None:
                data = response.json()
                if "data" in data:
                    return data["data"]  # Returns the array directly
                return data
        except Exception as e:
            print(f"Error fetching map data from API: {e}")

        # Fallback: load from local JSON
        if self.MAP_JSON.exists():
            try:
                with open(self.MAP_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    if "versions" in data and data["versions"]:
                        latest_version = max(
                            data["versions"],
                            key=lambda x: tuple(
                                map(int, x["api_version"].split('.')))
                        )
                    return latest_version["data"]

            except Exception as e:
                print(f"Error reading local map file: {e}")
                return None

        else:
            print(f"Local map file not found: {self.MAP_JSON}")
            return None

    def load_jobs(self):
        try:  # Try to get jobs data from API
            response = self.api_client.get_jobs_data()
            if response is not None:
                data = response.json()
                if "data" in data:
                    return data["data"]  # Returns the array directly
                return data
        except Exception as e:
            print(f"Error fetching jobs data from API: {e}")

    # Fallback: load from local JSON
        if self.JOBS_JSON.exists():
            try:
                with open(self.JOBS_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # Handle versioned structure (created by save_jobs_data)
                    if "versions" in data and data["versions"]:
                        latest_version = max(
                            data["versions"],
                            key=lambda x: tuple(
                                map(int, x["api_version"].split('.')))
                        )
                        # Return the jobs array from the wrapped structure
                        return latest_version["data"].get("jobs", [])

                    # Handle original structure from jobs.json
                    elif "data" in data:
                        return data["data"]  # Returns the array directly

            except Exception as e:
                print(f"Error reading local jobs file: {e}")
                return None
        else:
            print(f"Local jobs file not found: {self.JOBS_JSON}")
            return None

    def load_weather(self):
        try:  # Try to get weather data from API
            response = self.api_client.get_weather_data()
            if response is not None:
                data = response.json()
                if "data" in data:
                    return data["data"]  # Returns the array directly
                return data
        except Exception as e:
            print(f"Error fetching weather data from API: {e}")

        # Fallback: load from local JSON
        if self.WEATHER_JSON.exists():
            try:
                with open(self.WEATHER_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "versions" in data and data["versions"]:
                        latest_version = max(
                            data["versions"],
                            key=lambda x: tuple(
                                map(int, x["api_version"].split('.')))
                        )
                    return latest_version["data"]
            except Exception as e:
                print(f"Error reading local weather file: {e}")
                return None
        else:
            print(f"Local weather file not found: {self.WEATHER_JSON}")
            return None
