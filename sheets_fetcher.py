"""Fetch course configuration from Google Sheets for syllabus generation.

This module fetches data from the same Google Sheets used by CourseHub,
converting it to the format expected by the syllabus templates.
"""

import os
from typing import Any, Dict, List, Optional

import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",  # Read/write access
    "https://www.googleapis.com/auth/drive.readonly",
]


class SheetsFetcher:
    """Fetches course configuration from Google Sheets."""

    def __init__(self, credentials_path: str):
        """Initialize with service account credentials.

        Args:
            credentials_path: Path to service account JSON file
        """
        self._credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=SCOPES,
        )
        self._client = gspread.authorize(self._credentials)
        self._worksheet_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._current_sheet_id: Optional[str] = None

    def _prefetch_all_worksheets(self, sheet_id: str):
        """Fetch all worksheets from a spreadsheet in batch and cache them.

        This dramatically reduces API calls by fetching everything at once
        instead of one worksheet at a time.

        Args:
            sheet_id: Google Sheets document ID
        """
        if self._current_sheet_id == sheet_id and self._worksheet_cache:
            return  # Already cached

        self._worksheet_cache = {}
        self._current_sheet_id = sheet_id

        try:
            spreadsheet = self._client.open_by_key(sheet_id)
            worksheets = spreadsheet.worksheets()

            print(f"  Fetching {len(worksheets)} worksheets in batch...")

            for ws in worksheets:
                try:
                    # Get all values and convert to records format
                    values = ws.get_all_values()
                    if values and len(values) > 1:
                        headers = values[0]
                        records = []
                        for row in values[1:]:
                            # Create dict from headers and row values
                            record = {}
                            for i, header in enumerate(headers):
                                if header:  # Skip empty headers
                                    record[header] = row[i] if i < len(row) else ""
                            if any(record.values()):  # Skip empty rows
                                records.append(record)
                        self._worksheet_cache[ws.title] = records
                    else:
                        self._worksheet_cache[ws.title] = []
                except Exception as e:
                    print(f"  Warning: Could not fetch worksheet '{ws.title}': {e}")
                    self._worksheet_cache[ws.title] = []

        except Exception as e:
            print(f"  Error prefetching worksheets: {e}")
            raise

    def get_all_records(self, sheet_id: str, worksheet_name: str) -> List[Dict[str, Any]]:
        """Get all records from a worksheet as list of dicts.

        Uses cached data if available, otherwise fetches directly.

        Args:
            sheet_id: Google Sheets document ID
            worksheet_name: Name of the worksheet tab

        Returns:
            List of dictionaries (one per row, keys from header row)
        """
        # Use cache if available
        if self._current_sheet_id == sheet_id and worksheet_name in self._worksheet_cache:
            return self._worksheet_cache[worksheet_name]

        # Fallback to direct fetch (shouldn't normally happen after prefetch)
        spreadsheet = self._client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        return worksheet.get_all_records()

    def fetch_course_config(self, config_sheet_id: str, course_code: str, term: str) -> Dict[str, Any]:
        """Fetch complete course configuration and convert to syllabus format.

        Args:
            config_sheet_id: Google Sheets ID for course configuration
            course_code: Course code (e.g., "MATH 140B")
            term: Term string (e.g., "Spring 2026")

        Returns:
            Dictionary matching the syllabus YAML structure
        """
        # Prefetch all worksheets at once to minimize API calls
        self._prefetch_all_worksheets(config_sheet_id)

        config = {
            "course": self._fetch_course_info(config_sheet_id, course_code, term),
            "instructors": self._fetch_instructors(config_sheet_id),
            "mwf_sections": self._fetch_lecture_sections(config_sheet_id),
            "tuesday_sections": self._fetch_tuesday_sections(config_sheet_id),
            "exams": self._fetch_exams(config_sheet_id),
            "important_dates": self._fetch_important_dates(config_sheet_id),
            "policies": self._fetch_policies(config_sheet_id),
            "grading": self._fetch_grading(config_sheet_id),
            "learning_targets": self._fetch_learning_targets(config_sheet_id),
            "quiz_schedule": self._fetch_quiz_schedule(config_sheet_id),
            "la_sessions": self._fetch_la_sessions(config_sheet_id),
            # study_guides removed - now provided elsewhere
        }

        # Add office hours embed URL if available
        office_hours_url = self._get_office_hours_embed_url(config_sheet_id)
        if office_hours_url:
            config["office_hours_embed_url"] = office_hours_url
        else:
            config["office_hours_embed_url"] = ""

        return config

    def _fetch_course_info(self, sheet_id: str, course_code: str, term: str) -> Dict[str, Any]:
        """Fetch basic course info from Course Info tab."""
        try:
            records = self.get_all_records(sheet_id, "Course Info")
            # Course Info is typically key-value pairs in first two columns
            info = {}
            for record in records:
                # Handle both row-based and column-based formats
                if "Setting" in record and "Value" in record:
                    info[record["Setting"]] = record["Value"]
                else:
                    # First column is key, second is value
                    keys = list(record.keys())
                    if len(keys) >= 2:
                        info[record[keys[0]]] = record[keys[1]]

            # Course Name is the short form (e.g., "Math 140B") - used for display code
            # Course Title is the long form (e.g., "Calculus with Applications to Biology")
            course_name = info.get("Course Name", "")
            course_title = info.get("Course Title", "")

            # Format the code properly (e.g., "Math 140B" -> "MATH 140B")
            display_code = course_name.upper() if course_name else course_code

            # Parse prerequisites (can be newline or pipe separated for multiple items)
            prereqs_raw = info.get("Prerequisites", "")
            if prereqs_raw:
                # Split on newlines or pipes
                if "\n" in prereqs_raw:
                    prerequisites = [p.strip() for p in prereqs_raw.split("\n") if p.strip()]
                elif "|" in prereqs_raw:
                    prerequisites = [p.strip() for p in prereqs_raw.split("|") if p.strip()]
                else:
                    prerequisites = [prereqs_raw.strip()]
            else:
                prerequisites = []

            return {
                "code": display_code,
                "title": course_title,
                "term": info.get("Term", term),
                "includes_math197": str(info.get("Includes Math 197", "")).lower() in ("true", "yes", "1"),
                "course_hub_url": info.get("Course Hub URL", ""),
                "prerequisites": prerequisites,
            }
        except Exception as e:
            print(f"Warning: Could not fetch Course Info: {e}")
            return {"code": course_code, "term": term, "title": "", "includes_math197": False, "prerequisites": []}

    def _fetch_instructors(self, sheet_id: str) -> List[Dict[str, Any]]:
        """Fetch instructor information from Instructors tab, enriched with section details and office hours."""
        try:
            # First, build a mapping of section numbers to their details
            section_details = {}
            try:
                lecture_records = self.get_all_records(sheet_id, "Lecture Sections")
                for record in lecture_records:
                    section_num = str(record.get("Section", "")).strip()
                    if section_num:
                        section_details[section_num] = {
                            "number": section_num,
                            "days": record.get("Days", ""),
                            "time": record.get("Time", ""),
                            "location": record.get("Location", "TBD"),
                        }
            except Exception as e:
                print(f"Warning: Could not fetch Lecture Sections for instructor enrichment: {e}")

            # Build a mapping of instructor names to their office hours
            office_hours_by_instructor = {}
            try:
                oh_records = self.get_all_records(sheet_id, "Office Hours")
                for record in oh_records:
                    instructor_name = record.get("Instructor", "").strip()
                    if not instructor_name:
                        continue
                    if instructor_name not in office_hours_by_instructor:
                        office_hours_by_instructor[instructor_name] = []

                    # Build office hours entry with day, time, location, and type
                    oh_entry = {
                        "day": record.get("Day", ""),
                        "time": record.get("Time", ""),
                        "location": record.get("Location", ""),
                        "type": record.get("Type", "Drop-in"),  # Drop-in, Shared, Appointment needed
                    }
                    office_hours_by_instructor[instructor_name].append(oh_entry)
            except Exception as e:
                print(f"Warning: Could not fetch Office Hours: {e}")

            records = self.get_all_records(sheet_id, "Instructors")
            instructors = []
            for record in records:
                if not record.get("Name"):
                    continue
                instructor_name = record.get("Name", "")
                instructor = {
                    "id": record.get("ID", "").strip() or instructor_name.lower().replace(" ", "-"),
                    "name": instructor_name,
                    "title": record.get("Title", "Instructor"),
                    "email": record.get("Email", ""),
                    "office": record.get("Office", ""),
                }
                # Handle pronouns if present
                if record.get("Pronouns"):
                    instructor["pronouns"] = record.get("Pronouns")
                # Parse sections (comma, semicolon, or space separated) and enrich with details
                # Note: If Google Sheets interprets "1,5" as number 15, format the Sections column as Plain Text
                sections_str = str(record.get("Sections", ""))
                if sections_str:
                    # Try comma first, then semicolon, then space
                    if "," in sections_str:
                        section_nums = [s.strip() for s in sections_str.split(",") if s.strip()]
                    elif ";" in sections_str:
                        section_nums = [s.strip() for s in sections_str.split(";") if s.strip()]
                    elif " " in sections_str:
                        section_nums = [s.strip() for s in sections_str.split() if s.strip()]
                    else:
                        # Single section number
                        section_nums = [sections_str.strip()]
                    enriched_sections = []
                    for sec_num in section_nums:
                        if sec_num in section_details:
                            enriched_sections.append(section_details[sec_num])
                        else:
                            # Fallback if section details not found
                            enriched_sections.append({
                                "number": sec_num,
                                "days": "",
                                "time": "",
                                "location": "",
                            })
                    instructor["sections"] = enriched_sections
                else:
                    instructor["sections"] = []

                # Add office hours for this instructor
                instructor["office_hours"] = office_hours_by_instructor.get(instructor_name, [])

                instructors.append(instructor)
            return instructors
        except Exception as e:
            print(f"Warning: Could not fetch Instructors: {e}")
            return []

    def _fetch_lecture_sections(self, sheet_id: str) -> List[Dict[str, Any]]:
        """Fetch MWF lecture sections from Lecture Sections tab."""
        try:
            # First, build a mapping of section numbers to instructors from Instructors tab
            section_to_instructor = {}
            try:
                instructor_records = self.get_all_records(sheet_id, "Instructors")
                for record in instructor_records:
                    instructor_name = record.get("Name", "")
                    instructor_id = record.get("ID", "").strip() or instructor_name.lower().replace(" ", "-")
                    sections_str = str(record.get("Sections", ""))
                    if sections_str and instructor_name:
                        # Parse sections (comma, semicolon, or space separated)
                        if "," in sections_str:
                            section_nums = [s.strip() for s in sections_str.split(",") if s.strip()]
                        elif ";" in sections_str:
                            section_nums = [s.strip() for s in sections_str.split(";") if s.strip()]
                        elif " " in sections_str:
                            section_nums = [s.strip() for s in sections_str.split() if s.strip()]
                        else:
                            section_nums = [sections_str.strip()]
                        for sec_num in section_nums:
                            section_to_instructor[sec_num] = {
                                "name": instructor_name,
                                "id": instructor_id,
                            }
            except Exception as e:
                print(f"Warning: Could not fetch Instructors for section enrichment: {e}")

            records = self.get_all_records(sheet_id, "Lecture Sections")
            # Group sections by time range for display
            sections_by_period = {}
            for record in records:
                if not record.get("Section"):
                    continue

                section_num = str(record.get("Section", ""))
                time_str = record.get("Time", "")
                # Determine period (Morning, Mid-day, Afternoon, Evening)
                period = self._get_time_period(time_str)

                if period not in sections_by_period:
                    sections_by_period[period] = {
                        "name": f"{period} Classes" if period != "Late Morning" else "Late Morning Class",
                        "icon": {"Morning": "🌅", "Late Morning": "☀️", "Afternoon": "🌞", "Evening": "🌙"}.get(period, "📚"),
                        "time_range": "",
                        "sections": [],
                    }

                # Get instructor from Lecture Sections tab first, then fall back to Instructors mapping
                instructor_name = record.get("Instructor", "")
                instructor_id = record.get("Instructor ID", "")
                if not instructor_name or instructor_name == "TBD":
                    if section_num in section_to_instructor:
                        instructor_name = section_to_instructor[section_num]["name"]
                        instructor_id = section_to_instructor[section_num]["id"]
                    else:
                        instructor_name = "TBD"

                sections_by_period[period]["sections"].append({
                    "number": section_num,
                    "time": time_str,
                    "location": record.get("Location", "TBD"),
                    "instructor": instructor_name,
                    "instructor_id": instructor_id,
                })

            # Calculate time ranges
            for period_data in sections_by_period.values():
                times = [s["time"] for s in period_data["sections"] if s["time"]]
                if times:
                    period_data["time_range"] = self._calculate_time_range(times)

            # Sort by time period order
            period_order = ["Morning", "Late Morning", "Afternoon", "Evening"]
            sorted_sections = sorted(
                sections_by_period.values(),
                key=lambda x: period_order.index(x["name"].replace(" Classes", "").replace(" Class", "")) if x["name"].replace(" Classes", "").replace(" Class", "") in period_order else 99
            )

            return sorted_sections
        except Exception as e:
            print(f"Warning: Could not fetch Lecture Sections: {e}")
            return []

    def _fetch_tuesday_sections(self, sheet_id: str) -> List[Dict[str, Any]]:
        """Fetch Tuesday recitation sections from Session Configuration tab."""
        try:
            records = self.get_all_records(sheet_id, "Session Configuration")
            sections = []
            for record in records:
                # Filter for recitation sessions (typically "Recitation" type or "R" in identifier)
                session_type = record.get("Session Type", "")
                identifier = record.get("Identifier", "")
                if "Recitation" in session_type or identifier.endswith("R"):
                    sections.append({
                        "identifier": identifier,  # Keep full identifier like "1R", "7R"
                        "time": record.get("Time", ""),
                        "location": record.get("Location", "TBD"),
                    })
            return sections
        except Exception as e:
            print(f"Warning: Could not fetch Session Configuration: {e}")
            return []

    def _fetch_exams(self, sheet_id: str) -> Dict[str, Any]:
        """Fetch exam information from Exams tab."""
        result = {
            "midterms": [],
            "final": {"date": "To be announced (Check the Penn State Final Exam Schedule)"},
            "midterm1": {"display": "TBD"},
            "midterm2": {"display": "TBD"},
            "makeup_quiz_sessions": [],
        }

        try:
            records = self.get_all_records(sheet_id, "Exams")

            for record in records:
                event = record.get("Event", "")
                date_str = record.get("Date", "")

                if "Midterm 1" in event or "Midterm One" in event:
                    result["midterms"].append({
                        "name": "Midterm One",
                        "date": date_str,
                        "time": record.get("Time", ""),
                        "location": record.get("Location", ""),
                        "makeup_date": record.get("Makeup Date", ""),
                        "makeup_time": record.get("Makeup Time", ""),
                        "makeup_location": record.get("Makeup Location", ""),
                    })
                    result["midterm1"]["display"] = self._format_display_date(date_str)

                elif "Midterm 2" in event or "Midterm Two" in event:
                    result["midterms"].append({
                        "name": "Midterm Two",
                        "date": date_str,
                        "time": record.get("Time", ""),
                        "location": record.get("Location", ""),
                        "makeup_date": record.get("Makeup Date", ""),
                        "makeup_time": record.get("Makeup Time", ""),
                        "makeup_location": record.get("Makeup Location", ""),
                    })
                    result["midterm2"]["display"] = self._format_display_date(date_str)

                elif "Make-up Quiz Session" in event or "Makeup Quiz Session" in event:
                    result["makeup_quiz_sessions"].append({
                        "name": event,
                        "date": date_str,
                        "time": record.get("Time", ""),
                        "location": record.get("Location", ""),
                        "notes": record.get("Notes", ""),
                    })

                elif "Final" in event:
                    result["final"] = {
                        "date": date_str,
                        "time": record.get("Time", ""),
                        "location": record.get("Location", ""),
                    }

            return result
        except Exception as e:
            print(f"Warning: Could not fetch exams: {e}")
            return result

    def _fetch_important_dates(self, sheet_id: str) -> Dict[str, Any]:
        """Fetch key dates for navigation sidebar."""
        try:
            records = self.get_all_records(sheet_id, "Important Dates")

            # Build list of all dates for display
            all_dates = []
            for record in records:
                event = record.get("Event", "").strip()
                date_str = record.get("Date", "").strip()
                if event and date_str:
                    all_dates.append({
                        "event": event,
                        "date": date_str
                    })

            # Also extract specific named dates for template use
            dates = {
                "all": all_dates,
                "regular_drop": "",
                "late_drop": "",
                "finals_week": "",
            }

            for record in records:
                event = record.get("Event", "").lower()
                date_str = record.get("Date", "")

                if "regular drop" in event or "drop deadline" in event:
                    dates["regular_drop"] = self._format_short_date(date_str)
                elif "late drop" in event:
                    dates["late_drop"] = self._format_short_date(date_str)
                elif "finals" in event:
                    dates["finals_week"] = date_str

            return dates
        except Exception as e:
            print(f"Warning: Could not fetch important dates: {e}")
            return {"all": [], "regular_drop": "TBD", "late_drop": "TBD", "finals_week": "TBD"}

    def _fetch_policies(self, sheet_id: str) -> Dict[str, Any]:
        """Fetch policy information."""
        policies = {
            "thursday_quiz_hours": [],
        }

        # Fetch quiz hours from Session Configuration
        try:
            records = self.get_all_records(sheet_id, "Session Configuration")
            for record in records:
                session_type = record.get("Session Type", "")
                if "Quiz Hour" in session_type:
                    policies["thursday_quiz_hours"].append({
                        "time": record.get("Time", ""),
                        "location": record.get("Location", ""),
                    })
        except Exception as e:
            print(f"Warning: Could not fetch quiz hours: {e}")

        # Note: makeup_quiz_sessions are now fetched from Exams tab via _fetch_exams()

        return policies

    def _fetch_grading(self, sheet_id: str) -> Dict[str, Any]:
        """Fetch grading thresholds from Grade Thresholds tab."""
        grading = {
            "thresholds": {},
            "math197_thresholds": {},
            "xp": {
                "modifications": [],
                "activities": [],
            },
        }

        try:
            records = self.get_all_records(sheet_id, "Grade Thresholds")
            for record in records:
                grade = record.get("Grade", "")
                if not grade:
                    continue

                # Check if this is a Math 197 threshold
                is_197 = "197" in str(record.get("Course", ""))

                threshold = {
                    "complete": int(record.get("Number Complete", 0) or record.get("Min Complete", 0)) if (record.get("Number Complete") or record.get("Min Complete")) else None,
                    "proficient": int(record.get("Number Proficient", 0) or record.get("Min Proficient", 0)) if (record.get("Number Proficient") or record.get("Min Proficient")) else None,
                }

                if is_197:
                    grading["math197_thresholds"][grade] = threshold
                else:
                    grading["thresholds"][grade] = threshold
        except Exception as e:
            print(f"Warning: Could not fetch grade thresholds: {e}")

        # Fetch XP Activities
        try:
            xp_records = self.get_all_records(sheet_id, "XP Activities")
            for record in xp_records:
                activity = {
                    "name": record.get("Activity", ""),
                    "value": record.get("XP Value", ""),
                    "details": record.get("Details", ""),
                }
                if activity["name"]:
                    grading["xp"]["activities"].append(activity)
        except Exception as e:
            print(f"Warning: Could not fetch XP activities: {e}")

        # Fetch XP Modifications settings and generate table
        try:
            mod_records = self.get_all_records(sheet_id, "XP Modifications")
            xp_per_mod = 250  # default
            max_mods = 3  # default

            for record in mod_records:
                setting = record.get("Setting", "")
                value = record.get("Value", "")
                if "per modification" in setting.lower():
                    xp_per_mod = int(value)
                elif "maximum" in setting.lower():
                    max_mods = int(value)

            # Generate modifications table dynamically
            for i in range(max_mods + 1):
                if i == 0:
                    label = f"Less than {xp_per_mod} XP"
                elif i == max_mods:
                    threshold = max_mods * xp_per_mod
                    label = f"{threshold} or more XP"
                else:
                    low = i * xp_per_mod
                    high = (i + 1) * xp_per_mod - 1
                    label = f"{low}-{high} XP"

                grading["xp"]["modifications"].append({
                    "threshold": i * xp_per_mod,
                    "mods": i,
                    "label": label,
                    "max_mods": max_mods,
                })
        except Exception as e:
            print(f"Warning: Could not fetch XP modifications: {e}")
            # Fallback to default values
            grading["xp"]["modifications"] = [
                {"threshold": 0, "mods": 0, "label": "Less than 250 XP", "max_mods": 3},
                {"threshold": 250, "mods": 1, "label": "250-499 XP", "max_mods": 3},
                {"threshold": 500, "mods": 2, "label": "500-749 XP", "max_mods": 3},
                {"threshold": 750, "mods": 3, "label": "750 or more XP", "max_mods": 3},
            ]

        return grading

    def _fetch_learning_targets(self, sheet_id: str) -> Dict[str, Any]:
        """Fetch learning targets configuration."""
        lt_config = {
            "total": 25,
            "detailed_list_url": "",
            "essential": [],
            "targets": [],  # Full list of learning targets with details
        }

        try:
            records = self.get_all_records(sheet_id, "Learning Targets")
            lt_config["total"] = len(records)

            for record in records:
                # Handle both "LT ID" and "LT_ID" column names
                lt_id = record.get("LT ID", "") or record.get("LT_ID", "")
                if not lt_id:
                    continue

                # Check if this is an essential target
                is_essential = str(record.get("Essential", "")).lower() in ("true", "yes", "1", "x")
                if is_essential:
                    # Extract number from LT ID (e.g., "LT1" -> 1)
                    try:
                        lt_num = int("".join(filter(str.isdigit, lt_id)))
                        lt_config["essential"].append(lt_num)
                    except ValueError:
                        pass

                # Build full target entry
                target = {
                    "id": lt_id,
                    "type": record.get("Type", "Two-Part"),  # Two-Part, One-Time, Group
                    "title": record.get("Title", ""),
                    "description": record.get("Description", ""),
                }

                # Detailed info for Two-Part targets (F and Adv sections)
                # Handle multiple column name formats
                f_desc = record.get("F_Description", "") or record.get("F Description", "") or record.get("Foundational Description", "")
                f_obj_str = record.get("F_Objectives", "") or record.get("F Objectives", "") or record.get("Foundational Objectives", "")
                adv_desc = record.get("Adv_Description", "") or record.get("Adv Description", "") or record.get("Advanced Description", "")
                adv_obj_str = record.get("Adv_Objectives", "") or record.get("Adv Objectives", "") or record.get("Advanced Objectives", "")
                notes = record.get("Notes", "")

                if f_desc:
                    target["f_description"] = f_desc
                if adv_desc:
                    target["adv_description"] = adv_desc
                if notes:
                    target["notes"] = notes

                # Parse objectives lists (newline or semicolon separated)
                if f_obj_str:
                    target["f_objectives"] = self._parse_objectives_list(f_obj_str)
                if adv_obj_str:
                    target["adv_objectives"] = self._parse_objectives_list(adv_obj_str)

                lt_config["targets"].append(target)

        except Exception as e:
            print(f"Warning: Could not fetch learning targets: {e}")

        # Try to get detailed list URL from Course Info
        try:
            records = self.get_all_records(sheet_id, "Course Info")
            info = {str(r.get("Setting", "")): r.get("Value", "") for r in records}
            lt_config["detailed_list_url"] = info.get("Learning Targets URL", "") or info.get("Detailed List URL", "")
        except:
            pass

        return lt_config

    # _fetch_study_guides removed - study guides now provided elsewhere

    def _fetch_quiz_schedule(self, sheet_id: str) -> List[Dict[str, Any]]:
        """Fetch quiz schedule from Quiz Schedule tab.

        Returns a list of schedule rows grouped by week, matching the format
        used by CourseHub's quiz schedule display.
        """
        schedule = []

        try:
            records = self.get_all_records(sheet_id, "Quiz Schedule")

            # Group records by week
            weeks_data = {}
            for record in records:
                week_num = record.get("Week", "")
                if not week_num:
                    continue

                try:
                    week_num = int(week_num)
                except ValueError:
                    continue

                if week_num not in weeks_data:
                    weeks_data[week_num] = {
                        "week": week_num,
                        "tuesday_date": "",
                        "tuesday_lts": [],
                        "tuesday_new_lts": [],
                        "tuesday_notes": "",
                        "thursday_date": "",
                        "thursday_lts": [],
                        "thursday_new_lts": [],
                        "thursday_notes": "",
                        "exam_sessions": [],
                    }

                week_entry = weeks_data[week_num]
                session = record.get("Session", "").strip()
                session_lower = session.lower()
                date_str = record.get("Date", "")

                # Parse learning targets (comma-separated)
                lts_str = record.get("Learning Targets", "") or record.get("LTs", "")
                if lts_str:
                    lts = [lt.strip() for lt in str(lts_str).split(",") if lt.strip()]
                else:
                    lts = []

                # Parse new learning targets (comma-separated)
                # Note: Column name is "New Lts" (not "New LTs")
                new_lts_str = record.get("New Lts", "") or record.get("New LTs", "") or record.get("New", "")
                if new_lts_str:
                    new_lts = [lt.strip() for lt in str(new_lts_str).split(",") if lt.strip()]
                else:
                    new_lts = []

                notes = record.get("Notes", "")

                # Determine exam type from Session column
                exam_type = None
                if session_lower == "midterm":
                    exam_type = "midterm"
                elif session_lower == "make-up midterm":
                    exam_type = "makeup_midterm"
                elif session_lower == "make-up" or session_lower == "makeup":
                    exam_type = "makeup"
                elif session_lower == "final":
                    exam_type = "final"

                # Handle regular Tuesday/Thursday sessions
                if "tuesday" in session_lower:
                    week_entry["tuesday_date"] = date_str
                    week_entry["tuesday_lts"] = lts
                    week_entry["tuesday_new_lts"] = new_lts
                    week_entry["tuesday_notes"] = notes
                elif "thursday" in session_lower:
                    week_entry["thursday_date"] = date_str
                    week_entry["thursday_lts"] = lts
                    week_entry["thursday_new_lts"] = new_lts
                    week_entry["thursday_notes"] = notes

                # Handle exam sessions (Midterm, Make-up, Final, etc.)
                if exam_type:
                    exam_entry = {
                        "date": date_str,
                        "exam_type": exam_type,
                        "session_type": session,
                        "learning_targets": lts,
                        "notes": notes,
                    }
                    # Avoid duplicates
                    existing_dates = [e["date"] for e in week_entry["exam_sessions"]]
                    if date_str not in existing_dates:
                        week_entry["exam_sessions"].append(exam_entry)

            # Sort by week number and return as list
            schedule = [weeks_data[w] for w in sorted(weeks_data.keys())]

        except Exception as e:
            print(f"Warning: Could not fetch quiz schedule: {e}")

        return schedule

    def _fetch_la_sessions(self, sheet_id: str) -> Dict[str, Any]:
        """Fetch LA Community Learning Sessions from LA Sessions tab.

        Expected columns in 'LA Sessions' tab:
        - Days: e.g., "Tuesdays and Wednesdays" or "Tuesdays, Wednesdays, and Thursdays"
        - Time: e.g., "6:00 - 7:00 PM"

        The location can be specified in Course Info as "LA Session Location".

        Returns:
            Dictionary with 'location' and 'schedule' list, or empty dict if not found.
        """
        la_sessions = {
            "location": "",
            "schedule": [],
        }

        # Try to get location from Course Info
        try:
            records = self.get_all_records(sheet_id, "Course Info")
            for record in records:
                if "Setting" in record:
                    setting = record.get("Setting", "").strip()
                    if setting.lower() in ("la session location", "la sessions location", "la location"):
                        la_sessions["location"] = record.get("Value", "").strip()
                        break
        except Exception as e:
            print(f"Warning: Could not fetch LA Session Location from Course Info: {e}")

        # Fetch schedule from LA Sessions tab
        try:
            records = self.get_all_records(sheet_id, "LA Sessions")
            for record in records:
                days = record.get("Days", "").strip()
                # Handle both "Time" and "Times" column names
                time = record.get("Time", "").strip() or record.get("Times", "").strip()
                if days and time:
                    la_sessions["schedule"].append({
                        "days": days,
                        "time": time,
                    })

            # If no schedule found, return empty dict (template will handle missing data)
            if not la_sessions["schedule"]:
                return {}

        except Exception as e:
            print(f"Warning: Could not fetch LA Sessions: {e}")
            return {}

        return la_sessions

    def _get_office_hours_embed_url(self, sheet_id: str) -> str:
        """Get office hours embed URL from Course Info if available."""
        try:
            records = self.get_all_records(sheet_id, "Course Info")
            for record in records:
                if "Setting" in record and record["Setting"] == "Office Hours Embed URL":
                    return record.get("Value", "")
        except:
            pass
        return ""

    def _parse_objectives_list(self, objectives_str: str) -> List[str]:
        """Parse a string of objectives into a list.

        Handles newline-separated, semicolon-separated, or bullet-point formatted lists.
        """
        if not objectives_str:
            return []

        # Try splitting by newlines first
        if "\n" in objectives_str:
            items = objectives_str.split("\n")
        # Then try semicolons
        elif ";" in objectives_str:
            items = objectives_str.split(";")
        # Then try bullet points (common copy-paste from docs)
        elif "•" in objectives_str:
            items = objectives_str.split("•")
        elif "- " in objectives_str:
            items = objectives_str.split("- ")
        else:
            # Single item or comma-separated (less likely for long descriptions)
            items = [objectives_str]

        # Clean up each item
        cleaned = []
        for item in items:
            item = item.strip()
            # Remove leading bullets, dashes, or numbers
            if item and item[0] in "-•*":
                item = item[1:].strip()
            # Skip empty items
            if item:
                cleaned.append(item)

        return cleaned

    def _get_time_period(self, time_str: str) -> str:
        """Determine if a time is Morning, Mid-day, Afternoon, or Evening."""
        if not time_str:
            return "Morning"
        # Only look at the START time (before any dash or hyphen)
        start_time = time_str.split("-")[0].strip()
        start_time_lower = start_time.lower()
        # Extract hour from start time only
        try:
            hour_part = start_time.split(":")[0].strip()
            hour = int(hour_part)
            # Only check AM/PM in the start time portion
            if "pm" in start_time_lower and hour != 12:
                hour += 12
            elif "am" in start_time_lower and hour == 12:
                hour = 0

            if hour < 10:
                return "Morning"
            elif hour < 12:
                return "Late Morning"
            elif hour < 17:
                return "Afternoon"
            else:
                return "Evening"
        except:
            return "Morning"

    def _calculate_time_range(self, times: List[str]) -> str:
        """Calculate overall time range from list of times."""
        if not times:
            return ""
        # Simple: just use first and last times
        # Could be improved with actual time parsing
        return f"{times[0].split('-')[0].strip()} - {times[-1].split('-')[-1].strip()}"

    def _format_display_date(self, date_str: str) -> str:
        """Format date for display (e.g., 'Tuesday, February 17')."""
        # If already formatted, return as-is
        if any(day in date_str for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]):
            return date_str
        return date_str

    def _format_short_date(self, date_str: str) -> str:
        """Format date for short display (e.g., 'January 23')."""
        # Remove day of week if present
        for day in ["Monday, ", "Tuesday, ", "Wednesday, ", "Thursday, ", "Friday, ", "Saturday, ", "Sunday, "]:
            date_str = date_str.replace(day, "")
        return date_str.strip()


def fetch_config_from_sheets(
    course_id: str,
    config_sheet_id: str,
    credentials_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function to fetch course config from Google Sheets.

    Args:
        course_id: Course identifier (e.g., "math140b")
        config_sheet_id: Google Sheets ID for course configuration
        credentials_path: Path to service account JSON (uses env var if not provided)

    Returns:
        Dictionary matching the syllabus YAML structure
    """
    if credentials_path is None:
        credentials_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        if not credentials_path:
            raise ValueError(
                "No credentials path provided and GOOGLE_SERVICE_ACCOUNT_FILE not set"
            )

    # Expand ~ to home directory
    credentials_path = os.path.expanduser(credentials_path)

    # Determine course code and term from course_id
    course_map = {
        "math140b": ("MATH 140B", "Calculus with Applications to Biology"),
        "math141b": ("MATH 141B", "Calculus with Applications to Biology II"),
        "math198": ("MATH 198", "Special Topics"),
    }
    course_code, course_title = course_map.get(course_id.lower(), (course_id.upper(), ""))

    term = os.environ.get("SEMESTER_NAME", "Spring 2026")

    fetcher = SheetsFetcher(credentials_path)
    config = fetcher.fetch_course_config(config_sheet_id, course_code, term)

    # Set title if not fetched
    if not config["course"].get("title"):
        config["course"]["title"] = course_title

    return config
