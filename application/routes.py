from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from datetime import datetime
from application.model import *

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        facultyID = request.form.get('facultyID')
        password = request.form.get('password')
        
        faculty = Faculty.query.filter_by(id = facultyID).first()
        
        
        if(faculty.passcode == password):
            session['faculty_id'] = faculty.id
            return redirect(url_for("landingPage"))
        else:
            return render_template('login.html')

@app.route("/landingPage",methods = ['GET',"POST"])
def landingPage():
    if(request.method == 'POST'):
        return redirect(url_for('landingPage'))
    faculty = Faculty.query.filter_by(id = session['faculty_id']).first()
    exams  = Exam.query.filter_by(faculty_id = session['faculty_id']).all()
    return render_template('landing.html',faculty = faculty,exams = exams)

@app.route('/landingPage/new-exam',methods = ['POST'])
def new_exam():
    
    facultyID = session['faculty_id']
    
    year = request.form.get('year')
    section = request.form.get('section')
    
    date_string = request.form.get('date')
    date = datetime.strptime(date_string, '%Y-%m-%d').date()
    
    name = request.form.get('name')
    courseID = request.form.get('courseID')
    co1 = int(request.form.get('co1'))
    co2 = int(request.form.get('co2'))
    co3 = int(request.form.get('co3'))
    co4 = int(request.form.get('co4'))
    co5 = int(request.form.get('co5'))
    co6 = int(request.form.get('co6'))
    
    newExam = Exam(
        year = year,
        section = section,
        date = date,
        name = name,
        courseID = courseID,
        co1 = co1,
        co2 = co2,
        co3 = co3,
        co4 = co4,
        co5 = co5,
        co6 = co6,
        max_marks = co1+co2+co3+co4+co5+co6,
        faculty_id = facultyID
    )
    
    exams  = Exam.query.filter_by(faculty_id = session['faculty_id']).all()
    
    db.session.add(newExam)
    db.session.commit()
    return render_template('landing.html',faculty = facultyID,exams = exams)

@app.route("/landingPage/examsDetails", methods = ['GET'])
def examsDetails():
    faculty_id = session['faculty_id']
    faculty = Faculty.query.filter_by(id = faculty_id).first()
    examID = request.args.get('examID')
    exam = Exam.query.filter_by(id = examID).first()
    return render_template('examDetails.html',facultyName = faculty.name,exam = exam)

@app.route("/landingPage/examEdit", methods=['GET'])
def examEdit():
    examID = request.args.get('examID')
    exam = Exam.query.filter_by(id=examID).first()
    
    faculty_id = session['faculty_id']
    faculty = Faculty.query.filter_by(id=faculty_id).first()
    
    stream = Stream.query.filter_by(id=faculty.stream_id).first()
    
    teaches = Teaches.query.filter_by(faculty_id=faculty_id, year=exam.year, section=exam.section).first()
    
    course = Course.query.filter_by(course_id=exam.courseID).first()
    
    students = Student.query.filter_by(year=exam.year, section=exam.section, stream_id=stream.id).all()
    
    student_answers = []
    
    for student in students:
        answers = Answer.query.filter_by(student_id=student.id, exam_id=exam.id).all()
        student_answers_entry = {
            'studentID': student.id,
            'answers': answers,
            'co1': 0,
            'co2': 0,
            'co3': 0,
            'co4': 0,
            'co5': 0,
            'co6': 0,
            'questions': {answer.question_id: answer.marks for answer in answers}
        }
        for answer in answers:
            question = Question.query.filter_by(id=answer.question_id).first()
            student_answers_entry[f'co{question.co}'] += answer.marks
        student_answers.append(student_answers_entry)
    
    questions = Question.query.filter_by(exam_id=exam.id).all()
    
    return render_template('entermarks.html', facultyName=faculty.name, exam=exam, students=student_answers, questions=questions)

@app.route('/save_marks', methods=['POST'])
def save_marks():
    questions = Question.query.filter_by(exam_id=request.form.get('examID')).all()
    student_ids = request.form.getlist('student_ids[]')  # Get the student IDs
    for student_id in student_ids:
        student = Student.query.get(student_id)  # Fetch the student from the database
        
        # Update marks for each question for the student
        for question in range(1, len(questions) + 1):  # Adjust the range based on your question count
            marks = request.form.get(f'marks_{student_id}_Q{question}')
            if marks is not None:
                marks = float(marks)
                # Here, you can update the marks for the student and the question
                # Assuming you have a relationship for storing question marks
                student.set_marks(question, marks)
        
        # Recalculate the COs and total marks for the student
        co_values = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        
        for question in range(1, len(questions) + 1):
            question_marks = student.get_marks(question)
            question_co = Question.query.get(question).co  # Assume CO is an attribute in the Question model
            co_values[question_co] += question_marks
        
        # Update the CO values and total for the student
        student.update_CO_values(co_values)
        student.update_total_marks()

    # Commit changes to the database
    db.session.commit()

    # After saving, redirect or display a success message
    return redirect(url_for(landingPage))