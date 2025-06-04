from math import ceil
from pulp import LpProblem, LpMinimize, LpVariable, LpBinary, lpSum, LpStatus

def optimize_classrooms(courses, rooms):
    max_room_capacity = max(rooms.values())
    
    # Step 1: Split large courses into sections if needed
    expanded_courses = {}
    for code, data in courses.items():
        name = data["name"]
        enrollment = data["enrollment"]
        sessions = data["sessions"]
        time = data["time"]

        if enrollment <= max_room_capacity:
            expanded_courses[code] = {"name": name, "enrollment": enrollment, "sessions": sessions, "time": time}
        else:
            sections = ceil(enrollment / max_room_capacity)
            section_size = ceil(enrollment / sections)
            for i in range(sections):
                section_code = f"{code}_sec{i+1}"
                expanded_courses[section_code] = {
                    "name": f"{name} (Section {i+1})",
                    "enrollment": section_size,
                    "sessions": sessions,
                    "time": time
                }

    # Step 2: Build optimization model
    model = LpProblem("CourseRoomAssignmentWithSections", LpMinimize)

    x = {
        (course, room): LpVariable(f"x_{course}_{room}", cat=LpBinary)
        for course in expanded_courses
        for room in rooms
        if expanded_courses[course]["enrollment"] <= rooms[room]
    }

    slack = {
        course: LpVariable(f"slack_{course}", cat=LpBinary)
        for course in expanded_courses
    }

    penalty = 1e6

    model += lpSum(
        x[course, room] *
        (rooms[room] - expanded_courses[course]["enrollment"]) *
        expanded_courses[course]["sessions"]
        for (course, room) in x
    ) + lpSum(penalty * slack[course] for course in expanded_courses)

    for course in expanded_courses:
        model += lpSum(x[course, room] for room in rooms if (course, room) in x) + slack[course] == 1

    room_time_usage = {}
    for (course, room) in x:
        for t in expanded_courses[course]["time"]:
            room_time_usage.setdefault((room, t), []).append(x[course, room])
    for (room, t), vars_at_time in room_time_usage.items():
        model += lpSum(vars_at_time) <= 1

    model.solve()

    result = {
        "status": LpStatus[model.status],
        "assignments": [],
        "unassigned": [],
        "total_unused": 0
    }

    for (course, room), var in x.items():
        if var.value() == 1:
            unused = (rooms[room] - expanded_courses[course]["enrollment"]) * expanded_courses[course]["sessions"]
            result["assignments"].append({
                "course": expanded_courses[course]["name"],
                "room": room,
                "time": ", ".join(expanded_courses[course]["time"]),
                "unused_seat_hours": unused
            })
            result["total_unused"] += unused

    for course in expanded_courses:
        if slack[course].value() == 1:
            result["unassigned"].append({
                "course": expanded_courses[course]["name"],
                "time": ", ".join(expanded_courses[course]["time"])
            })

    return result
