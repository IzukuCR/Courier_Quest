"""
Data Manager module for handling game data from files and APIs.

This module manages all the game data like city maps, job listings,
weather information, and player scores. It can get data from the
internet or use local backup files if needed.
"""

import json
from pathlib import Path
from datetime import datetime
from .api_client import APIClient


class DataManager:
    """
    Manages all game data from files and internet sources.
    
    This class handles loading and saving game data. It uses
    the singleton pattern so there's only one data manager
    for the entire game. It tries to get fresh data from the
    internet but falls back to local files if needed.
    """
    _instance = None
    _initialized = False

    DATA_DIR = Path(__file__).parent.parent / "data"
    MAP_JSON = DATA_DIR / "cities.json"
    JOBS_JSON = DATA_DIR / "jobs.json"
    WEATHER_JSON = DATA_DIR / "weather.json"
    WEATHER_BURST_JSON = DATA_DIR / "burst.json"
    SCORES_JSON = DATA_DIR / "scores.json"

    def __init__(self):
        """
        Initialize the data manager (singleton pattern).
        
        This only runs once for the entire program since
        we use the singleton pattern.
        """
        if not DataManager._initialized:
            self.api_client = APIClient()
            DataManager._initialized = True

    def __new__(cls):
        # Singleton pattern
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        # Singleton access method
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reset(self):
        # Method to reset the singleton (for testing or re-initialization)
        DataManager._instance = None
        DataManager._initialized = False

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
            # Ensure data directory exists
            if not self.DATA_DIR.exists():
                self.DATA_DIR.mkdir(parents=True, exist_ok=True)

            # Load existing file or create new structure
            if json_file_path.exists() and json_file_path.stat().st_size > 0:
                try:
                    with open(json_file_path, "r", encoding="utf-8") as f:
                        file_data = json.load(f)
                except json.JSONDecodeError:
                    file_data = {"versions": []}
            else:
                file_data = {"versions": []}

            api_version = api_data.get("version", "1.0")
            new_content = api_data.get("data")
            # Check if this version exists AND if content is different
            should_save = True
            if file_data.get("versions"):
                for existing_version in file_data["versions"]:
                    if existing_version.get("api_version") == api_version:
                        existing_content = existing_version.get("data")

                        # Compare content, not just version
                        if existing_content == new_content:
                            print(f"{data_type.capitalize()} version {api_version} "
                                  f"with same content already exists")
                            should_save = False
                        else:
                            print(f"{data_type.capitalize()} version {api_version} "
                                  f"exists but content changed - updating")
                            # Remove old version to replace it
                            file_data["versions"].remove(existing_version)
                        break

            # Add new version if content is different or doesn't exist
            if should_save:
                new_version_entry = {
                    "entry_id": len(file_data.get("versions", [])) + 1,
                    "api_version": api_version,
                    "data": new_content,
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
                    f"{data_type.capitalize()} version {api_version} saved successfully")
                return True
            else:
                print(f"{data_type.capitalize()} - no changes detected")
                return False

        except Exception as e:
            print(f"Data Manager: Error adding {data_type} version: {e}")
            return False

    def save_map_data(self):
        try:
            response = self.api_client.get_map_data()
            if response is not None:
                api_data = response.json()
                return self._add_version_to_json(api_data, self.MAP_JSON, "map")
        except Exception as e:
            print(f"Data Manager: Error fetching map data from API: {e}")
        return False

    def save_jobs_data(self):
        try:
            response = self.api_client.get_jobs_data()
            if response is not None:
                api_data = response.json()

                # Where data is an array, not an object with version
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
            print(f"Data Manager: Error fetching jobs data from API: {e}")
        return False

    def save_weather_data_seed(self):
        try:
            response = self.api_client.get_weather_data_seed()
            if response is not None:
                api_data = response.json()
                return self._add_version_to_json(api_data, self.WEATHER_JSON, "weather")
        except Exception as e:
            print(
                f"Data Manager: Error fetching weather data (seed) from API: {e}")
        return False

    def save_weather_data_burst(self):
        try:
            response = self.api_client.get_weather_data_burst()
            if response is not None:
                api_data = response.json()
                return self._add_version_to_json(api_data, self.WEATHER_BURST_JSON, "weather")
        except Exception as e:
            print(
                f"Data Manager: Error fetching weather data (burst) from API: {e}")
        return False

    def load_city(self):
        try:  # Try to get map data from API
            response = self.api_client.get_map_data()
            if response is not None:
                data = response.json()
                self._add_version_to_json(data, self.MAP_JSON, "map")
                if "data" in data:
                    return data["data"]  # Returns the array directly
                return data
        except Exception as e:
            print(f"Data Manager: Error fetching map data from API: {e}")

        # Fallback: load from local JSON
        if self.MAP_JSON.exists():
            try:
                with open(self.MAP_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "versions" in data and data["versions"]:
                    # Versioned structure
                    latest_version = max(
                        data["versions"],
                        key=lambda x: tuple(
                            map(int, x["api_version"].split('.')))
                    )
                    return latest_version["data"]
                elif "data" in data:
                    # Old direct structure
                    return data["data"]
                else:
                    # Fallback: assume all content is data
                    return data
            except Exception as e:
                print(f"Data Manager: Error reading local map file: {e}")
                return None

        else:
            print(f"Data Manager: Local map file not found: {self.MAP_JSON}")
            return None

    def load_jobs(self):
        try:  # Try to get jobs data from API
            response = self.api_client.get_jobs_data()
            if response is not None:
                data = response.json()

                if isinstance(data, dict) and "data" in data and "version" in data:
                    # Wrap the structure to match expected format
                    wrapped_data = {
                        "data": {
                            "version": data.get("version", "1.0"),
                            "jobs": data.get("data", [])
                        }
                    }
                    self._add_version_to_json(
                        wrapped_data, self.JOBS_JSON, "jobs")
                else:
                    # If API returns different structure
                    self._add_version_to_json(data, self.JOBS_JSON, "jobs")

                if "data" in data:
                    return data["data"]  # Returns the array directly
                return data
        except Exception as e:
            print(f"Data Manager: Error fetching jobs data from API: {e}")

        # Fallback: load from local JSON
        if self.JOBS_JSON.exists():
            try:
                with open(self.JOBS_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if "versions" in data and data["versions"]:
                    # Versioned structure
                    latest_version = max(
                        data["versions"],
                        key=lambda x: tuple(
                            map(int, x["api_version"].split('.')))
                    )
                    # Jobs content might be nested
                    version_data = latest_version["data"]
                    return version_data.get("jobs", version_data)
                elif "data" in data:
                    # Old direct structure
                    return data["data"]
                else:
                    # Fallback: assume all content is data
                    return data

            except Exception as e:
                print(f"Data Manager: Error reading local jobs file: {e}")
                return None
        else:
            print(f"Data Manager: Local jobs file not found: {self.JOBS_JSON}")
            return None

    def load_weather(self):
        try:  # Try to get weather data from API
            response = self.api_client.get_weather_data_seed()
            if response is not None:
                data = response.json()
                self._add_version_to_json(
                    data, self.WEATHER_JSON, "weather seed")
                if "data" in data:
                    return data["data"]  # Returns the array directly
                return data
        except Exception as e:
            print(
                f"Data Manager: Error fetching weather (seed) data from API: {e}")

        # Fallback: load from local JSON
        if self.WEATHER_JSON.exists():
            try:
                with open(self.WEATHER_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "versions" in data and data["versions"]:
                    # Versioned structure
                    latest_version = max(
                        data["versions"],
                        key=lambda x: tuple(
                            map(int, x["api_version"].split('.')))
                    )
                    return latest_version["data"]
                elif "data" in data:
                    # Old direct structure
                    return data["data"]
                else:
                    # Fallback: assume all content is data
                    return data
            except Exception as e:
                print(
                    f"Data Manager: Error reading local weather (seed) file: {e}")
                return None
        else:
            print(
                f"Data Manager: Local weather (seed) file not found: {self.WEATHER_JSON}")
            return None

    def load_weather_burst(self):
        try:  # Try to get weather data from API
            response = self.api_client.get_weather_data_burst()
            if response is not None:
                data = response.json()
                self._add_version_to_json(
                    data, self.WEATHER_BURST_JSON, "weather burst")
                if "data" in data:
                    return data["data"]  # Returns the array directly
                return data
        except Exception as e:
            print(
                f"Data Manager: Error fetching weather (burst) data from API: {e}")

        # Fallback: load from local JSON
        if self.WEATHER_BURST_JSON.exists():
            try:
                with open(self.WEATHER_BURST_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "versions" in data and data["versions"]:
                    # Versioned structure
                    latest_version = max(
                        data["versions"],
                        key=lambda x: tuple(
                            map(int, x["api_version"].split('.')))
                    )
                    return latest_version["data"]
                elif "data" in data:
                    # Old direct structure
                    return data["data"]
                else:
                    # Fallback: assume all content is data
                    return data
            except Exception as e:
                print(
                    f"Data Manager: Error reading local weather (burst) file: {e}")
                return None
        else:
            print(
                f"Data Manager: Local weather (burst) file not found: {self.WEATHER_BURST_JSON}")
            return None

    def save_score(self, player_name: str, score: int, stats: dict) -> bool:
        """Save a player's score with detailed statistics"""
        try:
            if not self.SCORES_JSON.parent.exists():
                self.SCORES_JSON.parent.mkdir(parents=True, exist_ok=True)

            # Load existing scores
            scores_data = []
            if self.SCORES_JSON.exists():
                try:
                    with open(self.SCORES_JSON, 'r', encoding='utf-8') as f:
                        scores_data = json.load(f)
                except json.JSONDecodeError:
                    scores_data = []

            # Create new score entry
            score_entry = {
                "player_name": player_name,
                "score": score,
                "date": datetime.now().isoformat(),
                "stats": stats
            }

            # Add new score
            scores_data.append(score_entry)

            # Sort by score (highest first)
            scores_data.sort(key=lambda x: x["score"], reverse=True)

            # Save updated scores
            with open(self.SCORES_JSON, 'w', encoding='utf-8') as f:
                json.dump(scores_data, f, indent=4)

            print(f"Score saved successfully for {player_name}: {score}")
            return True

        except Exception as e:
            print(f"Error saving score: {e}")
            return False

    def delete_score(self, player_name: str, score: int, date: str) -> bool:
        """Delete a specific score entry"""
        try:
            if self.SCORES_JSON.exists():
                with open(self.SCORES_JSON, 'r', encoding='utf-8') as f:
                    scores_data = json.load(f)

                # Find and remove the matching score entry
                for score_entry in scores_data[:]:
                    if (score_entry.get('player_name') == player_name and
                        score_entry.get('score') == score and
                            score_entry.get('date') == date):
                        scores_data.remove(score_entry)
                        break

                # Save updated scores
                with open(self.SCORES_JSON, 'w', encoding='utf-8') as f:
                    json.dump(scores_data, f, indent=4)

                print(f"Score deleted successfully for {player_name}")
                return True

        except Exception as e:
            print(f"Error deleting score: {e}")
        return False

    def load_scores(self) -> list:
        """Load and return all saved scores"""
        try:
            if self.SCORES_JSON.exists():
                with open(self.SCORES_JSON, 'r', encoding='utf-8') as f:
                    scores_data = json.load(f)
                return scores_data
            return []
        except Exception as e:
            print(f"Error loading scores: {e}")
            return []

    def get_high_scores(self, limit: int = 10) -> list:
        """Get the top N scores"""
        scores = self.load_scores()
        return sorted(scores, key=lambda x: x["score"], reverse=True)[:limit]
