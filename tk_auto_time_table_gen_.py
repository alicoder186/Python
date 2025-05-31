import random
from tabulate import tabulate
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import mysql.connector

class UniversityTimetableGenerator:
    def __init__(self):
        self.courses = {} 
        self.faculty = {}  
        self.programs = {} 
        self.rooms = []    
        self.time_slots = []
        self.timetable = defaultdict(dict)  
        
    def add_course(self, code, name, credits, lecture_hours, lab_hours=0):
        self.courses[code] = {
            'name': name,
            'credits': credits,
            'lecture_hours': lecture_hours,
            'lab_hours': lab_hours,
            'sections': []
        }
    
    def add_faculty(self, faculty_id, name, availability=None):
        self.faculty[faculty_id] = {
            'name': name,
            'availability': availability if availability else {}
        }
    
    def add_program(self, program_id, name, semesters):
        self.programs[program_id] = {
            'name': name,
            'semesters': semesters
        }
    
    def add_room(self, room_id, capacity, room_type='lecture'):
        self.rooms.append({
            'id': room_id,
            'capacity': capacity,
            'type': room_type
        })
    
    def set_time_slots(self, days, start_times, duration, slot_type='lecture'):
        for day in days:
            for time in start_times:
                self.time_slots.append({
                    'day': day,
                    'start': time,
                    'end': self._calculate_end_time(time, duration),
                    'type': slot_type
                })
    
    def _calculate_end_time(self, start_time, duration):
        hours, minutes = map(int, start_time.split(':'))
        total_minutes = hours * 60 + minutes + duration
        return f"{total_minutes//60:02d}:{total_minutes%60:02d}"
    
    def generate_semester_timetable(self, program_id, semester):
        if program_id not in self.programs:
            raise ValueError("Program not found")
        if semester not in self.programs[program_id]['semesters']:
            raise ValueError("Semester not found in program")
        
        courses = self.programs[program_id]['semesters'][semester]
        
        if semester not in self.timetable:
            self.timetable[semester] = {}
        if program_id not in self.timetable[semester]:
            self.timetable[semester][program_id] = defaultdict(dict)
        
        for course_code in courses:
            if course_code not in self.courses:
                continue
                
            course = self.courses[course_code]
            
            for _ in range(course['lecture_hours']):
                self._assign_course_slot(
                    program_id, semester, course_code, 
                    is_lab=False, course=course
                )
            
            for _ in range(course['lab_hours']):
                self._assign_course_slot(
                    program_id, semester, course_code, 
                    is_lab=True, course=course
                )
    
    def _assign_course_slot(self, program_id, semester, course_code, is_lab, course):
        slot_type = 'lab' if is_lab else 'lecture'
        available_slots = [
            slot for slot in self.time_slots 
            if slot['type'] == slot_type 
            and not self._is_slot_taken(semester, program_id, slot)
        ]
        
        if not available_slots:
            print(f"Warning: Could not assign all hours for {course_code}")
            return
        
        chosen_slot = random.choice(available_slots)
        
        entry = {
            'course': course_code,
            'course_name': course['name'],
            'type': 'Lab' if is_lab else 'Lecture',
            'room': self._find_available_room(slot_type),
            'faculty': self._assign_faculty(course_code)
        }
        
        day = chosen_slot['day']
        time_key = f"{chosen_slot['start']}-{chosen_slot['end']}"
        
        if time_key not in self.timetable[semester][program_id][day]:
            self.timetable[semester][program_id][day][time_key] = entry
    
    def _is_slot_taken(self, semester, program_id, slot):
        day = slot['day']
        time_key = f"{slot['start']}-{slot['end']}"
        
        if semester in self.timetable and \
           program_id in self.timetable[semester] and \
           day in self.timetable[semester][program_id] and \
           time_key in self.timetable[semester][program_id][day]:
            return True
        return False
    
    def _find_available_room(self, room_type):
        rooms = [r for r in self.rooms if r['type'] == room_type]
        return random.choice(rooms)['id'] if rooms else "TBD"
    
    def _assign_faculty(self, course_code):
        available_faculty = [f for f in self.faculty.values()]
        return random.choice(available_faculty)['name'] if available_faculty else "TBD"
    
    def get_semester_timetable_text(self, program_id, semester):
        if semester not in self.timetable or program_id not in self.timetable[semester]:
            return "No timetable generated for this program/semester"
        
        program_name = self.programs[program_id]['name']
        result = f"Timetable for {program_name} - Semester {semester}\n"
        result += "=" * 50 + "\n"
        
        days = sorted(self.timetable[semester][program_id].keys())
        
        header = ["Time"] + days
        table_data = []
        
        all_time_slots = set()
        for day in days:
            all_time_slots.update(self.timetable[semester][program_id][day].keys())
        time_slots = sorted(all_time_slots)
        
        for time_slot in time_slots:
            row = [time_slot]
            for day in days:
                entry = self.timetable[semester][program_id][day].get(time_slot, {})
                if entry:
                    cell = (
                        f"{entry['course_name']}\n"
                        f"{entry['type']} ({entry['course']})\n"
                        f"Room: {entry['room']}\n"
                        f"Faculty: {entry['faculty']}"
                    )
                else:
                    cell = "Free"
                row.append(cell)
            table_data.append(row)
        
        result += tabulate(table_data, headers=header, tablefmt="grid")
        return result

class TimetableGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("University Timetable Generator - AI, SE & CS Programs")
        self.root.geometry("1000x700")
        
        self.generator = UniversityTimetableGenerator()
        
        self.create_widgets()
        self.setup_programs_data()
    
    def create_widgets(self):
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_courses_tab()
        self.create_faculty_tab()
        self.create_programs_tab()
        self.create_rooms_tab()
        self.create_timeslots_tab()
        self.create_generate_tab()
    
    def create_courses_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Courses")
        
        # Add course frame
        add_frame = ttk.LabelFrame(tab, text="Add New Course")
        add_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(add_frame, text="Course Code:").grid(row=0, column=0, padx=5, pady=5)
        self.course_code = ttk.Entry(add_frame)
        self.course_code.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Course Name:").grid(row=1, column=0, padx=5, pady=5)
        self.course_name = ttk.Entry(add_frame)
        self.course_name.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Credits:").grid(row=2, column=0, padx=5, pady=5)
        self.course_credits = ttk.Entry(add_frame)
        self.course_credits.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Lecture Hours:").grid(row=3, column=0, padx=5, pady=5)
        self.lecture_hours = ttk.Entry(add_frame)
        self.lecture_hours.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Lab Hours:").grid(row=4, column=0, padx=5, pady=5)
        self.lab_hours = ttk.Entry(add_frame)
        self.lab_hours.grid(row=4, column=1, padx=5, pady=5)
        self.lab_hours.insert(0, "0")
        
        ttk.Button(add_frame, text="Add Course", command=self.add_course).grid(row=5, columnspan=2, pady=10)
        
        # View courses frame
        view_frame = ttk.LabelFrame(tab, text="Current Courses")
        view_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Code", "Name", "Credits", "Lecture Hours", "Lab Hours")
        self.courses_tree = ttk.Treeview(view_frame, columns=columns, show="headings")
        
        for col in columns:
            self.courses_tree.heading(col, text=col)
            self.courses_tree.column(col, width=120)
        
        self.courses_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_faculty_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Faculty")
        
        # Add faculty frame
        add_frame = ttk.LabelFrame(tab, text="Add New Faculty")
        add_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(add_frame, text="Faculty ID:").grid(row=0, column=0, padx=5, pady=5)
        self.faculty_id = ttk.Entry(add_frame)
        self.faculty_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Faculty Name:").grid(row=1, column=0, padx=5, pady=5)
        self.faculty_name = ttk.Entry(add_frame)
        self.faculty_name.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(add_frame, text="Add Faculty", command=self.add_faculty).grid(row=2, columnspan=2, pady=10)
        
        # View faculty frame
        view_frame = ttk.LabelFrame(tab, text="Current Faculty")
        view_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Name")
        self.faculty_tree = ttk.Treeview(view_frame, columns=columns, show="headings")
        
        for col in columns:
            self.faculty_tree.heading(col, text=col)
            self.faculty_tree.column(col, width=120)
        
        self.faculty_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_programs_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Programs")
        
        # Add program frame
        add_frame = ttk.LabelFrame(tab, text="Add New Program")
        add_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(add_frame, text="Program ID:").grid(row=0, column=0, padx=5, pady=5)
        self.program_id = ttk.Entry(add_frame)
        self.program_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Program Name:").grid(row=1, column=0, padx=5, pady=5)
        self.program_name = ttk.Entry(add_frame)
        self.program_name.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Semesters:").grid(row=2, column=0, padx=5, pady=5)
        self.semesters = ttk.Entry(add_frame)
        self.semesters.grid(row=2, column=1, padx=5, pady=5)
        self.semesters.insert(0, "1,2,3,4,5,6,7,8")
        
        ttk.Button(add_frame, text="Add Program", command=self.add_program).grid(row=3, columnspan=2, pady=10)
        
        # View programs frame
        view_frame = ttk.LabelFrame(tab, text="Current Programs")
        view_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Name", "Semesters")
        self.programs_tree = ttk.Treeview(view_frame, columns=columns, show="headings")
        
        for col in columns:
            self.programs_tree.heading(col, text=col)
            self.programs_tree.column(col, width=120)
        
        self.programs_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_rooms_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Rooms")
        
        # Add room frame
        add_frame = ttk.LabelFrame(tab, text="Add New Room")
        add_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(add_frame, text="Room ID:").grid(row=0, column=0, padx=5, pady=5)
        self.room_id = ttk.Entry(add_frame)
        self.room_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Capacity:").grid(row=1, column=0, padx=5, pady=5)
        self.room_capacity = ttk.Entry(add_frame)
        self.room_capacity.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Room Type:").grid(row=2, column=0, padx=5, pady=5)
        self.room_type = ttk.Combobox(add_frame, values=["lecture", "lab"])
        self.room_type.grid(row=2, column=1, padx=5, pady=5)
        self.room_type.set("lecture")
        
        ttk.Button(add_frame, text="Add Room", command=self.add_room).grid(row=3, columnspan=2, pady=10)
        
        # View rooms frame
        view_frame = ttk.LabelFrame(tab, text="Current Rooms")
        view_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Capacity", "Type")
        self.rooms_tree = ttk.Treeview(view_frame, columns=columns, show="headings")
        
        for col in columns:
            self.rooms_tree.heading(col, text=col)
            self.rooms_tree.column(col, width=120)
        
        self.rooms_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_timeslots_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Time Slots")
        
        # Add timeslot frame
        add_frame = ttk.LabelFrame(tab, text="Add Time Slots")
        add_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(add_frame, text="Days (comma separated):").grid(row=0, column=0, padx=5, pady=5)
        self.days_entry = ttk.Entry(add_frame)
        self.days_entry.grid(row=0, column=1, padx=5, pady=5)
        self.days_entry.insert(0, "Monday,Tuesday,Wednesday,Thursday,Friday")
        
        ttk.Label(add_frame, text="Start Times (comma separated):").grid(row=1, column=0, padx=5, pady=5)
        self.start_times = ttk.Entry(add_frame)
        self.start_times.grid(row=1, column=1, padx=5, pady=5)
        self.start_times.insert(0, "09:00,11:00,14:00,16:00")
        
        ttk.Label(add_frame, text="Duration (minutes):").grid(row=2, column=0, padx=5, pady=5)
        self.duration = ttk.Entry(add_frame)
        self.duration.grid(row=2, column=1, padx=5, pady=5)
        self.duration.insert(0, "60")
        
        ttk.Label(add_frame, text="Slot Type:").grid(row=3, column=0, padx=5, pady=5)
        self.slot_type = ttk.Combobox(add_frame, values=["lecture", "lab"])
        self.slot_type.grid(row=3, column=1, padx=5, pady=5)
        self.slot_type.set("lecture")
        
        ttk.Button(add_frame, text="Add Time Slots", command=self.add_time_slots).grid(row=4, columnspan=2, pady=10)
        
        # View timeslots frame
        view_frame = ttk.LabelFrame(tab, text="Current Time Slots")
        view_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Day", "Start", "End", "Type")
        self.timeslots_tree = ttk.Treeview(view_frame, columns=columns, show="headings")
        
        for col in columns:
            self.timeslots_tree.heading(col, text=col)
            self.timeslots_tree.column(col, width=120)
        
        self.timeslots_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_generate_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Generate Timetable")
        
        # Generate frame
        gen_frame = ttk.LabelFrame(tab, text="Generate Timetable")
        gen_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(gen_frame, text="Program:").grid(row=0, column=0, padx=5, pady=5)
        self.program_combo = ttk.Combobox(gen_frame)
        self.program_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(gen_frame, text="Semester:").grid(row=1, column=0, padx=5, pady=5)
        self.semester_combo = ttk.Combobox(gen_frame, values=[str(i) for i in range(1, 9)])
        self.semester_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(gen_frame, text="Generate Timetable", command=self.generate_timetable).grid(row=2, columnspan=2, pady=10)
        
        # Display frame
        display_frame = ttk.LabelFrame(tab, text="Timetable")
        display_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.timetable_display = scrolledtext.ScrolledText(display_frame, wrap=tk.WORD)
        self.timetable_display.pack(fill=tk.BOTH, expand=True)
    
    def setup_programs_data(self):
        # Add BS Artificial Intelligence program
        self.generator.add_program("AI", "BS Artificial Intelligence", {
            1: ["CS101", "MATH101", "PHYS101", "ENG101", "AI101"],
            2: ["CS102", "MATH102", "PHYS102", "HUM101", "AI102"],
            3: ["CS201", "MATH201", "STAT201", "AI201", "AI211"],
            4: ["CS202", "MATH202", "AI202", "AI212", "AI222"],
            5: ["AI301", "ML301", "AI311", "AI321", "ELECTIVE1"],
            6: ["AI302", "ML302", "AI312", "NLP301", "ELECTIVE2"],
            7: ["AI401", "AI411", "AI421", "PROJ401", "ELECTIVE3"],
            8: ["AI402", "AI412", "PROJ402", "SEMINAR", "ELECTIVE4"]
        })
        
        # Add BS Software Engineering program
        self.generator.add_program("SE", "BS Software Engineering", {
            1: ["CS101", "MATH101", "ENG101", "SE101", "HUM101"],
            2: ["CS102", "MATH102", "SE102", "SE112", "SE122"],
            3: ["CS201", "SE201", "SE211", "SE221", "SE231"],
            4: ["CS202", "SE202", "SE212", "SE222", "SE232"],
            5: ["SE301", "SE311", "SE321", "SE331", "ELECTIVE1"],
            6: ["SE302", "SE312", "SE322", "SE332", "ELECTIVE2"],
            7: ["SE401", "SE411", "SE421", "PROJ401", "ELECTIVE3"],
            8: ["SE402", "SE412", "PROJ402", "SEMINAR", "ELECTIVE4"]
        })
        
        # Add BS Computer Science program
        self.generator.add_program("CS", "BS Computer Science", {
            1: ["CS101", "MATH101", "PHYS101", "ENG101", "HUM101"],
            2: ["CS102", "MATH102", "PHYS102", "CS112", "CS122"],
            3: ["CS201", "MATH201", "CS211", "CS221", "CS231"],
            4: ["CS202", "CS212", "CS222", "CS232", "CS242"],
            5: ["CS301", "CS311", "CS321", "CS331", "ELECTIVE1"],
            6: ["CS302", "CS312", "CS322", "CS332", "ELECTIVE2"],
            7: ["CS401", "CS411", "CS421", "PROJ401", "ELECTIVE3"],
            8: ["CS402", "CS412", "PROJ402", "SEMINAR", "ELECTIVE4"]
        })
        
        # Add common courses (CS, Math, etc.)
        self.generator.add_course("CS101", "Introduction to Programming", 3, 3)
        self.generator.add_course("CS102", "Object-Oriented Programming", 4, 3, 2)
        self.generator.add_course("CS201", "Data Structures & Algorithms", 4, 3, 2)
        self.generator.add_course("CS202", "Database Systems", 4, 3, 2)
        self.generator.add_course("CS211", "Computer Organization", 3, 3)
        self.generator.add_course("CS221", "Discrete Mathematics", 3, 3)
        self.generator.add_course("CS231", "Operating Systems", 4, 3, 2)
        self.generator.add_course("CS301", "Theory of Computation", 3, 3)
        self.generator.add_course("CS302", "Compiler Construction", 4, 3, 2)
        self.generator.add_course("CS311", "Computer Networks", 4, 3, 2)
        self.generator.add_course("CS321", "Software Engineering", 3, 3)
        self.generator.add_course("CS331", "Artificial Intelligence", 3, 3)
        self.generator.add_course("CS401", "Advanced Algorithms", 3, 3)
        self.generator.add_course("CS402", "Distributed Systems", 3, 3)
        self.generator.add_course("CS411", "Computer Security", 3, 3)
        self.generator.add_course("CS421", "Cloud Computing", 3, 3)
        
        # Add Math courses
        self.generator.add_course("MATH101", "Calculus I", 4, 4)
        self.generator.add_course("MATH102", "Calculus II", 4, 4)
        self.generator.add_course("MATH201", "Linear Algebra", 3, 3)
        self.generator.add_course("MATH202", "Probability & Statistics", 3, 3)
        
        # Add Physics courses
        self.generator.add_course("PHYS101", "Physics I", 4, 3, 2)
        self.generator.add_course("PHYS102", "Physics II", 4, 3, 2)
        
        # Add General Education courses
        self.generator.add_course("ENG101", "English Composition", 3, 3)
        self.generator.add_course("HUM101", "Introduction to Humanities", 3, 3)
        
        # Add AI-specific courses
        self.generator.add_course("AI101", "Introduction to AI", 3, 3)
        self.generator.add_course("AI102", "AI Programming", 4, 3, 2)
        self.generator.add_course("AI201", "Machine Learning Fundamentals", 3, 3)
        self.generator.add_course("AI202", "Knowledge Representation", 3, 3)
        self.generator.add_course("AI211", "AI Mathematics", 3, 3)
        self.generator.add_course("AI212", "Cognitive Science", 3, 3)
        self.generator.add_course("AI222", "Computer Vision", 3, 3)
        self.generator.add_course("AI301", "Advanced Machine Learning", 4, 3, 2)
        self.generator.add_course("AI302", "Deep Learning", 4, 3, 2)
        self.generator.add_course("AI311", "Reinforcement Learning", 3, 3)
        self.generator.add_course("AI312", "Natural Language Processing", 3, 3)
        self.generator.add_course("AI321", "Robotics", 4, 3, 2)
        self.generator.add_course("AI401", "AI Ethics", 3, 3)
        self.generator.add_course("AI402", "Advanced AI Systems", 3, 3)
        self.generator.add_course("AI411", "AI Research Methods", 3, 3)
        self.generator.add_course("AI412", "AI Applications", 3, 3)
        self.generator.add_course("AI421", "Neural Networks", 3, 3)
        self.generator.add_course("ML301", "Machine Learning", 3, 3)
        self.generator.add_course("ML302", "Advanced ML", 3, 3)
        self.generator.add_course("NLP301", "Natural Language Processing", 3, 3)
        
        # Add SE-specific courses
        self.generator.add_course("SE101", "Introduction to SE", 3, 3)
        self.generator.add_course("SE102", "Software Requirements", 3, 3)
        self.generator.add_course("SE112", "Software Design", 3, 3)
        self.generator.add_course("SE122", "Software Testing", 3, 3)
        self.generator.add_course("SE201", "Software Architecture", 3, 3)
        self.generator.add_course("SE202", "Software Quality Assurance", 3, 3)
        self.generator.add_course("SE211", "Human-Computer Interaction", 3, 3)
        self.generator.add_course("SE212", "Software Metrics", 3, 3)
        self.generator.add_course("SE221", "Software Process", 3, 3)
        self.generator.add_course("SE222", "Software Maintenance", 3, 3)
        self.generator.add_course("SE231", "Web Development", 4, 3, 2)
        self.generator.add_course("SE232", "Mobile Development", 4, 3, 2)
        self.generator.add_course("SE301", "Software Project Management", 3, 3)
        self.generator.add_course("SE302", "Enterprise Architecture", 3, 3)
        self.generator.add_course("SE311", "DevOps", 4, 3, 2)
        self.generator.add_course("SE312", "Cloud Native Development", 3, 3)
        self.generator.add_course("SE321", "Software Security", 3, 3)
        self.generator.add_course("SE322", "Software Verification", 3, 3)
        self.generator.add_course("SE331", "Big Data Systems", 3, 3)
        self.generator.add_course("SE332", "IoT Systems", 3, 3)
        self.generator.add_course("SE401", "Software Economics", 3, 3)
        self.generator.add_course("SE402", "Software Innovation", 3, 3)
        self.generator.add_course("SE411", "Agile Methods", 3, 3)
        self.generator.add_course("SE412", "Software Leadership", 3, 3)
        self.generator.add_course("SE421", "Software Standards", 3, 3)
        
        # Add project and elective courses
        self.generator.add_course("PROJ401", "Project I", 3, 1, 4)
        self.generator.add_course("PROJ402", "Project II", 3, 1, 4)
        self.generator.add_course("ELECTIVE1", "Technical Elective I", 3, 3)
        self.generator.add_course("ELECTIVE2", "Technical Elective II", 3, 3)
        self.generator.add_course("ELECTIVE3", "Technical Elective III", 3, 3)
        self.generator.add_course("ELECTIVE4", "Technical Elective IV", 3, 3)
        self.generator.add_course("SEMINAR", "Research Seminar", 1, 1)
        
        # Add faculty
        self.generator.add_faculty("F1", "Dr. AI Expert")
        self.generator.add_faculty("F2", "Prof. Software Architect")
        self.generator.add_faculty("F3", "Dr. Algorithm Specialist")
        self.generator.add_faculty("F4", "Prof. Database Guru")
        self.generator.add_faculty("F5", "Dr. Machine Learning Researcher")
        self.generator.add_faculty("F6", "Prof. Systems Engineer")
        self.generator.add_faculty("F7", "Dr. Natural Language Processing Expert")
        self.generator.add_faculty("F8", "Prof. Cybersecurity Specialist")
        
        # Add rooms
        self.generator.add_room("A101", 50)
        self.generator.add_room("A102", 50)
        self.generator.add_room("A103", 50)
        self.generator.add_room("A104", 50)
        self.generator.add_room("B201", 30, "lab")
        self.generator.add_room("B202", 30, "lab")
        self.generator.add_room("B203", 30, "lab")
        self.generator.add_room("B204", 30, "lab")
        self.generator.add_room("AI_LAB1", 20, "lab")
        self.generator.add_room("SE_LAB1", 20, "lab")
        self.generator.add_room("CS_LAB1", 20, "lab")

        # Set time slots
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        lecture_times = ["08:00", "10:00", "13:00", "15:00"]
        lab_times = ["09:00", "11:00", "14:00", "16:00"]
        
        self.generator.set_time_slots(days, lecture_times, 60)
        self.generator.set_time_slots(days, lab_times, 120, "lab")
        
        self.refresh_all_views()
    
    def refresh_all_views(self):
        # Refresh courses tree
        self.courses_tree.delete(*self.courses_tree.get_children())
        for code, course in self.generator.courses.items():
            self.courses_tree.insert("", tk.END, values=(
                code, 
                course['name'], 
                course['credits'], 
                course['lecture_hours'], 
                course['lab_hours']
            ))
        
        # Refresh faculty tree
        self.faculty_tree.delete(*self.faculty_tree.get_children())
        for fid, faculty in self.generator.faculty.items():
            self.faculty_tree.insert("", tk.END, values=(fid, faculty['name']))
        
        # Refresh programs tree
        self.programs_tree.delete(*self.programs_tree.get_children())
        for pid, program in self.generator.programs.items():
            semesters = ", ".join(str(s) for s in program['semesters'].keys())
            self.programs_tree.insert("", tk.END, values=(pid, program['name'], semesters))
        
        # Refresh rooms tree
        self.rooms_tree.delete(*self.rooms_tree.get_children())
        for room in self.generator.rooms:
            self.rooms_tree.insert("", tk.END, values=(room['id'], room['capacity'], room['type']))
        
        # Refresh timeslots tree
        self.timeslots_tree.delete(*self.timeslots_tree.get_children())
        for slot in self.generator.time_slots:
            self.timeslots_tree.insert("", tk.END, values=(
                slot['day'], 
                slot['start'], 
                slot['end'], 
                slot['type']
            ))
        
        # Refresh program combo
        programs = list(self.generator.programs.keys())
        self.program_combo['values'] = programs
        if programs:
            self.program_combo.set(programs[0])
    
    def add_course(self):
        try:
            code = self.course_code.get().strip()
            name = self.course_name.get().strip()
            credits = int(self.course_credits.get())
            lecture_hours = int(self.lecture_hours.get())
            lab_hours = int(self.lab_hours.get())
            
            if not code or not name:
                raise ValueError("Course code and name are required")
            
            self.generator.add_course(code, name, credits, lecture_hours, lab_hours)
            self.refresh_all_views()
            messagebox.showinfo("Success", "Course added successfully")
            
            # Clear fields
            self.course_code.delete(0, tk.END)
            self.course_name.delete(0, tk.END)
            self.course_credits.delete(0, tk.END)
            self.lecture_hours.delete(0, tk.END)
            self.lab_hours.delete(0, tk.END)
            self.lab_hours.insert(0, "0")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
    
    def add_faculty(self):
        try:
            faculty_id = self.faculty_id.get().strip()
            name = self.faculty_name.get().strip()
            
            if not faculty_id or not name:
                raise ValueError("Faculty ID and name are required")
            
            self.generator.add_faculty(faculty_id, name)
            self.refresh_all_views()
            messagebox.showinfo("Success", "Faculty added successfully")
            
            # Clear fields
            self.faculty_id.delete(0, tk.END)
            self.faculty_name.delete(0, tk.END)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
    
    def add_program(self):
        try:
            program_id = self.program_id.get().strip()
            name = self.program_name.get().strip()
            semesters = self.semesters.get().strip()
            
            if not program_id or not name or not semesters:
                raise ValueError("All fields are required")
            
            semester_list = [s.strip() for s in semesters.split(",")]
            semester_dict = {}
            
            for sem in semester_list:
                semester_dict[int(sem)] = []  # Empty course list for now
            
            self.generator.add_program(program_id, name, semester_dict)
            self.refresh_all_views()
            messagebox.showinfo("Success", "Program added successfully")
            
            # Clear fields
            self.program_id.delete(0, tk.END)
            self.program_name.delete(0, tk.END)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
    
    def add_room(self):
        try:
            room_id = self.room_id.get().strip()
            capacity = int(self.room_capacity.get())
            room_type = self.room_type.get()
            
            if not room_id:
                raise ValueError("Room ID is required")
            
            self.generator.add_room(room_id, capacity, room_type)
            self.refresh_all_views()
            messagebox.showinfo("Success", "Room added successfully")
            
            # Clear fields
            self.room_id.delete(0, tk.END)
            self.room_capacity.delete(0, tk.END)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
    
    def add_time_slots(self):
        try:
            days = [d.strip() for d in self.days_entry.get().split(",")]
            start_times = [t.strip() for t in self.start_times.get().split(",")]
            duration = int(self.duration.get())
            slot_type = self.slot_type.get()
            
            if not days or not start_times:
                raise ValueError("Days and start times are required")
            
            self.generator.set_time_slots(days, start_times, duration, slot_type)
            self.refresh_all_views()
            messagebox.showinfo("Success", "Time slots added successfully")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
    
    def generate_timetable(self):
        try:
            program_id = self.program_combo.get()
            semester = int(self.semester_combo.get())
            
            if not program_id:
                raise ValueError("Please select a program")
            
            self.generator.generate_semester_timetable(program_id, semester)
            timetable_text = self.generator.get_semester_timetable_text(program_id, semester)
            
            self.timetable_display.delete(1.0, tk.END)
            self.timetable_display.insert(tk.END, timetable_text)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

def main():
    root = tk.Tk()
    app = TimetableGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()