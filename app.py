# from fastapi import FastAPI, HTTPException, APIRouter
import requests
from PyPDF2 import PdfReader
from general_reporter import get_general_reporter
from patient_tab import get_patient_text
from parent import get_parent_text
import spacy
import pysftp
# from fastapi import FastAPI
import json
import streamlit as st
import tornado
from tornado.web import RequestHandler, Application
from tornado.routing import Rule, PathMatches
import gc


# Create a FastAPI instance

# C:\Users\kathiaja\Downloads\Pvtest-main\Pvtest-main\main.py


@st.cache_resource()
def setup_api_handler(uri, handler):
    print("Setup Tornado. Should be called only once")

    # Get instance of Tornado
    tornado_app = next(o for o in gc.get_referrers(Application) if o.__class__ is Application)

    # Setup custom handler
    tornado_app.wildcard_router.rules.insert(0, Rule(PathMatches(uri), handler))
# Tornado handler with PDF extraction functionality
class PdfExtractionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")

    def options(self, *args):
        self.set_header("Access-Control-Allow-Methods", "*")
        self.set_header("Access-Control-Request-Credentials", "true")
        self.set_header("Access-Control-Allow-Private-Network", "true")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_status(204)  # No Content

    def post(self, pdf_info):
        try:
            # Your existing pdf_extraction code
            # Replace 'pdf_info' with the actual value or information you want to pass
            pdf_extraction(pdf_info)

        except Exception as e:
            self.set_status(500)
            self.write(f"Error processing PDF: {str(e)}")


def pdf_extraction(pdf_info: str):
    print("pdf_info from method",pdf_info)
    try:

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        ftp = pysftp.Connection('testnovumgen.topiatech.co.uk', username='pvtestuser', password='Umlup01cli$$6969',
                                cnopts=cnopts)
        print("111111111111")
        with ftp.cd('/var/sftp/upload/pvtestusers/'):
            files = ftp.listdir()
            for file in files:
                if pdf_info in file:
                    ftp.get(file)
                    print('yes downloaded both files')
                    if 'Weekly' in file:
                        weekly_reader = file
                    else:
                        source_document = file
        weekly_reader = PdfReader(weekly_reader)
        source_file_reader = PdfReader(source_document)
        # weekly_reader = PdfReader('Weekly literature hits PDF.pdf')
        weekly_reader_num_pages = len(weekly_reader.pages)
        print("222222222222222")

        source_file_num_pages = len(source_file_reader.pages)
        weekly_text = ""
        all_text = ""
        nlp = spacy.load("en_core_web_sm")
        nlp_1 = spacy.load("en_ner_bc5cdr_md-0.5.3/en_ner_bc5cdr_md/en_ner_bc5cdr_md-0.5.3")
        # Loop through all pages and extract text
        for page_num in range(source_file_num_pages):
            page = source_file_reader.pages[page_num]
            text = page.extract_text()
            all_text += text
        for page_num in range(weekly_reader_num_pages):
            page = weekly_reader.pages[page_num]
            text = page.extract_text()
            weekly_text += text
        meta = source_file_reader.metadata
        general_extraction, reporter_extraction = get_general_reporter(
            source_text=all_text,
            weekly_text_1=weekly_text,
            en_core=nlp,
            meta_data=meta
        )
        # print(general_extraction, reporter_extraction)
        patient_extraction = get_patient_text(source_text=all_text, en_core=nlp, bcd5r=nlp_1)
        parent_extraction = get_parent_text(source_text=all_text, en_core=nlp, bcd5r=nlp_1)

        response_for_integration = {
            "general_information": general_extraction,
            "reporter": reporter_extraction,
            "patient": patient_extraction,
            "parent": parent_extraction
        }

        url = "https://demo1.topiatech.co.uk/PV/createCaseAI"
        print(
            "=--------------------------------------------------------------------------------------------------------")
        # Send the POST request with JSON data
        response = requests.post(url, json=response_for_integration)
        json_response_from_api = response.json()
        print("*" * 50)
        # Check the response status code
        if json_response_from_api['statusCode'] == 200:
            # Request was successful
            print("API request successful.")
            print("Status Code:", json_response_from_api['statusCode'])
            print("Response Headers:", response.headers)
            return {'statusCode': json_response_from_api['statusCode'], 'body': json.dumps(
                {"data": 'API request successful', "error ": {'msg': str("Status Code: " + json_response_from_api['statusCode'])},
                 "status": 5})}

        else:
            # Request failed
            print(f"API request failed with status code {json_response_from_api['statusCode']}: {json_response_from_api['message']}")
            print(response.text)

        #   if ftp:
        #         ftp.close()

        return {'statusCode': json_response_from_api['statusCode'], 'body': json.dumps({"data": 'API request success ', "error ": {
            'msg': str(f"API request success with status code {json_response_from_api['statusCode']}: {json_response_from_api['message']}")}, "status": json_response_from_api['statusCode']})}

    except Exception as e:
        return {'statusCode': 404, 'body': json.dumps({"data": 'failed ', "error ": {'msg': str(e)}, "status": 4})}


# New Tornado handler for handling GET requests
class GetHandler(RequestHandler):
    def get(self, data):
        try:
            # Handle GET request logic here
            self.write(f"Handling GET request with data: {data}")
        except Exception as e:
            self.set_status(500)
            self.write(f"Error processing GET request: {str(e)}")


setup_api_handler('/api/pdf_extraction/([^/]+)?', PdfExtractionHandler)
setup_api_handler('/api/get_demo/([^/]+)?', GetHandler)
