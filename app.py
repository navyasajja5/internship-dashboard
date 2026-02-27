import streamlit as st
import json
import os
import PyPDF2
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from io import BytesIO

DATA_FILE = "data.json"

# ---------------- LOAD & SAVE DATA ----------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data.setdefault("students", {})
    data.setdefault("companies", {})
    data.setdefault("governments", {})
    data.setdefault("internships", {})
    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------- PDF GENERATION ----------------
def generate_offer_letter(student_name, internship, company_name):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>ZenithSkill AI</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("<b>OFFER LETTER</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.5 * inch))

    text = f"""
    Dear {student_name},<br/><br/>
    Congratulations! You have been selected for the internship:
    <b>{internship['name']}</b><br/><br/>
    Company: <b>{company_name}</b><br/>
    Stipend: ₹{internship['stipend']}<br/><br/>
    We welcome you to ZenithSkill AI Internship Program.<br/><br/>
    Best Regards,<br/>
    Team ZenithSkill AI
    """

    elements.append(Paragraph(text, styles["Normal"]))
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_certificate(student_name, internship, company_name):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>ZenithSkill AI</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("<b>INTERNSHIP COMPLETION CERTIFICATE</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.5 * inch))

    text = f"""
    This is to certify that <b>{student_name}</b> has successfully completed
    the internship titled <b>{internship['name']}</b> at
    <b>{company_name}</b> under ZenithSkill AI.<br/><br/>
    The intern has demonstrated strong dedication,
    technical skills, and professionalism throughout the program.<br/><br/>
    We wish them continued success.
    """

    elements.append(Paragraph(text, styles["Normal"]))
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ---------------- RESUME MATCHER ----------------
def calculate_match(resume_text, required_skills):
    if not resume_text or not required_skills:
        return 0

    resume_text = resume_text.lower()
    matched = 0

    for skill in required_skills:
        if skill.lower() in resume_text:
            matched += 1

    return int((matched / len(required_skills)) * 100)


# ---------------- APP START ----------------
data = load_data()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "email" not in st.session_state:
    st.session_state.email = None


# ---------------- LOGIN / REGISTER ----------------
if not st.session_state.logged_in:

    st.title("ZenithSkill AI")

    role = st.selectbox("Select Role", ["Student", "Company", "Government"])
    if role =="Student":
        role_key ="students"
    elif role =="Company":
        role_key ="companies"
    else:
        role_key ="governments"
    
    action = st.radio("Action", ["Login", "Register"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    role_map = {
        "Student":"students",
        "Company":"companies",
        "Government":"governments"
    }
    role_key =role_map[role]

    if action == "Register":
        name = st.text_input("Full Name")
        if st.button("Register"):
            if email in data[role_key]:
                st.error("User already exists")
            else:
                data[role_key][email] = {
                    "name": name,
                    "password": password,
                    "wallet": 0,
                    "status": "Not Applied",
                    "internship_id": None,
                    "resume_text": "",
                    "match_percent": 0,
                    "task_solution": "",
                    "task_submitted": False,
                    "task_approved": False,
                    "stipend_paid": False,
                    "certificate_generated": False,
                    "offer_letter": False
                }
                save_data(data)
                st.success("Registered Successfully")

    if action == "Login":
        if st.button("Login"):
            users =data.get(role_key,{})
            if email in users and users[email]["password"] ==password:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Invalid Credentials")


# ---------------- DASHBOARD ----------------
else:

    role = st.session_state.role
    email = st.session_state.email

    st.sidebar.write("Logged in as:", role)
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # ================= STUDENT =================
    if role == "Student":

        student = data["students"][email]

        menu = st.sidebar.selectbox("Menu", [
            "View Internship",
            "Applications",
            "Task Submission",
            "Certificate Download",
            "My Wallet"
        ])

        # VIEW INTERNSHIPS
        if menu == "View Internship":
            for iid, internship in data["internships"].items():
                st.subheader(internship["name"])
                st.write("Description:", internship["internship_description"])
                st.write("Task:", internship["task_description"])
                st.write("Skills:", ", ".join(internship["required_skills"]))
                st.write("Stipend:", internship["stipend"])
                st.write("Task Reward:", internship["reward"])

                if st.button(f"Apply {iid}"):
                    student["status"] = "Applied"
                    student["internship_id"] = iid
                    save_data(data)
                    st.success("Applied Successfully")
                    st.rerun()

        # APPLICATIONS
        elif menu == "Applications":
            st.write("Status:", student["status"])

            resume = st.file_uploader("Upload Resume PDF", type=["pdf"])
            if resume:
                reader = PyPDF2.PdfReader(resume)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                student["resume_text"] = text

                if student["internship_id"]:
                    internship = data["internships"][student["internship_id"]]
                    match = calculate_match(text, internship["required_skills"])
                    student["match_percent"] = match
                    st.success(f"Resume Match: {match}%")

                save_data(data)

            if student["offer_letter"]:
                internship = data["internships"][student["internship_id"]]
                pdf = generate_offer_letter(
                    student["name"],
                    internship,
                    internship["company"]
                )
                st.download_button("Download Offer Letter", pdf, "Offer_Letter.pdf")

        # TASK SUBMISSION
        elif menu == "Task Submission":
            if student["status"] == "Approved":
                solution = st.text_area("Write Your Task Solution")

                if st.button("Submit Task"):
                    student["task_solution"] = solution
                    student["task_submitted"] = True
                    save_data(data)
                    st.success("Task Submitted Successfully")
                    st.rerun()

            else:
                st.warning("You are not approved yet.")

        # CERTIFICATE
        elif menu == "Certificate Download":
            if student["certificate_generated"]:
                internship = data["internships"][student["internship_id"]]
                pdf = generate_certificate(
                    student["name"],
                    internship,
                    internship["company"]
                )
                st.download_button("Download Certificate", pdf, "Certificate.pdf")
            else:
                st.warning("Certificate not available yet.")

        elif menu == "My Wallet":
            st.success(f"Wallet Balance: ₹{student['wallet']}")

    # ================= COMPANY =================
    elif role == "Company":

        menu = st.sidebar.selectbox("Menu", [
            "Post Internship",
            "View Applications",
            "Review Submission",
            "Internship Completion"
        ])

        if menu == "Post Internship":
            name = st.text_input("Internship Name")
            desc = st.text_area("Internship Description")
            task = st.text_area("Task Description")
            skills = st.text_input("Required Skills (comma separated)")
            stipend = st.number_input("Stipend", min_value=0)
            reward = st.number_input("Task Reward", min_value=0)

            if st.button("Post Internship"):
                iid = f"{name}_{len(data['internships'])}"
                data["internships"][iid] = {
                    "name": name,
                    "internship_description": desc,
                    "task_description": task,
                    "required_skills": [s.strip() for s in skills.split(",")],
                    "stipend": stipend,
                    "reward": reward,
                    "company": email
                }
                save_data(data)
                st.success("Internship Posted")

        if menu == "View Applications":
            for s_email, s_data in data["students"].items():
                if s_data["status"] == "Applied" and s_data["internship_id"]:
                    st.write(s_email, "- Match:", s_data["match_percent"], "%")
                    if st.button(f"Approve {s_email}"):
                        s_data["status"] = "Approved"
                        save_data(data)
                        st.success("Student Approved")

        if menu == "Review Submission":
            for s_email, s_data in data["students"].items():
                if s_data["task_submitted"] and not s_data["task_approved"]:
                    st.subheader(s_email)
                    st.write("Task Solution:")
                    st.write(s_data["task_solution"])

                    if st.button(f"Approve Task {s_email}"):
                        s_data["task_approved"] = True
                        s_data["offer_letter"] = True
                        internship = data["internships"][s_data["internship_id"]]
                        s_data["wallet"] += internship["reward"]
                        save_data(data)
                        st.success("Task Approved")

        if menu == "Internship Completion":
            for s_email, s_data in data["students"].items():
                if s_data["task_approved"] and not s_data["stipend_paid"]:
                    if st.button(f"Complete Internship {s_email}"):
                        internship = data["internships"][s_data["internship_id"]]
                        s_data["wallet"] += internship["stipend"]
                        s_data["stipend_paid"] = True
                        s_data["certificate_generated"] = True
                        save_data(data)
                        st.success("Internship Completed")

    # ================= GOVERNMENT =================
    elif role == "Government":

        menu = st.sidebar.selectbox("Menu", [
            "Dashboard",
            "CSR Analytics",
            "User Data",
            "Internships"
        ])

        if menu == "Dashboard":
            st.write("Total Students:", len(data["students"]))
            st.write("Total Companies:", len(data["companies"]))
            st.write("Total Internships:", len(data["internships"]))

        if menu == "CSR Analytics":
            total = sum(s["wallet"] for s in data["students"].values())
            st.write("Total CSR Distributed:", total)

        if menu == "User Data":
            st.json(data)

        if menu == "Internships":
            st.json(data["internships"])