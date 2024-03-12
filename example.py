import streamlit as st
import nltk
import spacy
import re
nltk.download('stopwords')
spacy.load('en_core_web_sm')

import pandas as pd
import base64, random
import time, datetime
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io, random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
import pafy
import plotly.express as px

nltk.download('stopwords')

def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

connection = pymysql.connect(host='localhost', user='root', password='Harini@13')
cursor = connection.cursor()

def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses, education):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
    name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills,
    courses, education)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


st.set_page_config(
    page_title="Smart Resume Analyzer",
  #  page_icon='./Logo/SRA_Logo.ico',
)

def extract_education(text):
    # Regular expression to find education information
    education_pattern = r'(?i)education\s*([\s\S]*?)(?=\n\n|\n[A-Z]|$)'
    matches = re.findall(education_pattern, text)

    education_list = []

    for match in matches:
        # Remove extra whitespaces and newlines
        cleaned_match = ' '.join(line.strip() for line in match.split('\n'))

        # Check if the cleaned match is not empty
        if cleaned_match:
            education_info = {
                "education_details": cleaned_match
            }
            education_list.append(education_info)

    return education_list

def extract_email(text):
    # Regular expression to find an email address in the text
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    if match:
        return match.group(0)
    else:
        return None

def chatbot_logic(question):
    # A simple rule-based chatbot logic
 
    # Check if the question contains both "education" and "skills"
    if "education" in question.lower() and "skills" in question.lower():
        # Extract education and skills conditions from the question
        match = re.search(r'education\s*([^\.]+).*skills\s*([^\.]+)', question, re.IGNORECASE)
        if match:
            education_condition = match.group(1).strip()
            skills_condition = match.group(2).strip()
 
            # Debugging print statements
            print("Education Condition:", education_condition)
            print("Skills Condition:", skills_condition)
 
            # Implement logic to fetch data based on the user's conditions
            # Iterate over each user record to check for matching education condition
            condition_query = f"WHERE Actual_skills LIKE '%{skills_condition}%'"
            query = f"SELECT * FROM user_data {condition_query};"
 
            cursor.execute(query)
            user_details = cursor.fetchall()
 
            matching_users = []
            for details in user_details:
                _, name, email, resume_score, timestamp, page_no, reco_field, cand_level, skills, recommended_skills, recommended_courses, education_list = details
                # Debugging print statement
                print("Education Details:", education_list)
 
                # Check if any education detail contains the specified condition
                matching_education = any(education_detail.get('education_details', '').lower().find(education_condition.lower()) != -1 for education_detail in education_list)
 
                if matching_education:
                    matching_users.append(details)
 
            if matching_users:
                response = "Details for users based on the conditions:\n"
                for details in matching_users:
                    _, name, email, resume_score, timestamp, page_no, reco_field, cand_level, skills, recommended_skills, recommended_courses, education = details
                    response += f"\nName: {name}\n"
                    response += f"Email: {email}\n"
                    response += f"Resume Score: {resume_score}\n"
                    response += f"Timestamp: {timestamp}\n"
                    response += f"Candidate Level: {cand_level}\n"
                    response += f"Skills: {skills}\n"
                    response += f"Recommended Skills: {recommended_skills}\n"
                    response += f"Education: {education}\n"
            else:
                response = "No users found based on the specified conditions."
        else:
            response = "Sorry, I couldn't extract valid education and skills conditions from your question."
 
    else:
        response = "Please provide a valid query with both 'education' and 'skills' conditions, such as 'Get details for users with education [condition] and skills [condition]'."
 
    return response

 
def run():
    st.title("Smart Resume Analyzer Chatbot")
    # ... (existing code)
   


    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)
    connection.select_db("sra")

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     education varchar(500) NOT NULL,
                     PRIMARY KEY (ID), UNIQUE(Email_id));
                    """
    cursor.execute(table_sql)

    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin", "Chatbot"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    

    if choice == 'Chatbot':
        st.header("Chat with the Resume Analyzer")
        user_question = st.text_input("Ask a question:")

        if st.button("Ask"):
            # Implement logic to fetch data based on the user's question
            answer = chatbot_logic(user_question)
            st.success(answer)


    elif choice == 'Normal User':
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smart recommendation based on it."</h4>''',
        #             unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                except:
                    pass

                education = extract_education(resume_text)
                print("Education:", education)



                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                   # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',
                    #            unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    #st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                     #           unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                  #  st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                   #             unsafe_allow_html=True)

                #st.subheader("**Skills Recommendation💡**")
                ## Skill shows
                keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=resume_data['skills'], key='1')

                ##  recommendation
                ds_keyword = ['data analysis', 'power bi', 'mysql', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''
                ## Courses recommendation
                for i in resume_data['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        #st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        #st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        #st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        #st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        #st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        break

                #
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ### Resume writing recommendation
               # st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score + 20

                if 'Declaration' in resume_text:
                    resume_score = resume_score + 20

                if 'Hobbies' or 'Interests' in resume_text:
                    resume_score = resume_score + 20

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 20
                if 'Projects' in resume_text:
                    resume_score = resume_score + 20

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                    str(resume_data['no_of_pages']), reco_field, cand_level,
                    str(resume_data['skills']), str(recommended_skills), str(rec_course), str(education))

                connection.commit()
            else:
                st.error('Something went wrong..')

    elif choice == 'Admin':
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'crossroad' and ad_password == 'abc123':
                st.success("Welcome Crossroad Elf")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course', 'education'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

            else:
                st.error("Wrong ID & Password Provided")


run()

