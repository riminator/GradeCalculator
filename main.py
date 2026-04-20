import requests

# =========================
# CONFIG (FILL THESE IN)
# =========================
CANVAS_URL = "https://utexas.instructure.com/"
API_TOKEN = "1017~6nUrXLYhYDXDf3wY4eTf68AkYnyruv6tJPBKcuzvhHvNUPUGazLWk8QnYTACGkEX"
COURSE_ID = "1442211"
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# =========================
# FETCH ASSIGNMENTS
# =========================
def get_assignments(course_id):
    url = f"{CANVAS_URL}/api/v1/courses/{course_id}/assignments?include[]=submission"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Error fetching assignments: {response.text}")

    return response.json()

# =========================
# PRINT EVERYTHING
# =========================
def print_assignments(assignments):
    print("\n📘 Assignment Grades\n")
    print("-" * 60)

    total_points = 0
    earned_points = 0

    for a in assignments:
        name = a.get("name", "Unknown Assignment")
        points_possible = a.get("points_possible", 0)

        submission = a.get("submission", {})
        score = submission.get("score")

        # Handle missing grades
        if score is None:
            score_display = "Not graded / Missing"
            score_val = 0
        else:
            score_display = f"{score}/{points_possible}"
            score_val = score

        print(f"{name}")
        print(f"   Score: {score_display}")
        print("-" * 60)

        # accumulate totals
        if points_possible:
            total_points += points_possible
            earned_points += score_val if score is not None else 0

    # final grade
    if total_points > 0:
        final_grade = (earned_points / total_points) * 100
        print(f"\n🎯 Final Grade: {final_grade:.2f}%")
    else:
        print("\nNo graded assignments found.")


def main():
    assignments = get_assignments(COURSE_ID)
    print_assignments(assignments)


if __name__ == "__main__":
    main()