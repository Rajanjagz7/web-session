"""
Selenium script — OzMed Create 50 Australian Patients
Registers 50 patients with full Australian health data and saves results to CSV + JSON.

Install:
    pip install selenium webdriver-manager

Run:
    python selenium_create_50_patients.py
"""

import csv
import json
import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

URL            = "https://practice2.dev.ozmed.health/"
SCREENSHOT_DIR = "patient_screenshots"
RESULTS_CSV    = "patient_results.csv"
RESULTS_JSON   = "patient_results.json"
PASSWORD       = "Test@Patient2024!"

# ── 50 Australian patients ────────────────────────────────────────────────────
PATIENTS = [
    # ── NSW ──────────────────────────────────────────────────────────────────
    {
        "title": "Mr",  "first_name": "James",     "last_name": "Wilson",
        "preferred_name": "James",  "dob": "14/03/1985", "gender": "Male",
        "email": "james.wilson.test01@testpatient.com.au", "phone": "0412345678",
        "address": "12 Harbour Street",  "suburb": "Sydney",       "state": "NSW", "postcode": "2000",
        "medicare": "2345678901", "medicare_ref": "1",
        "emergency_name": "Claire Wilson",  "emergency_phone": "0412111001", "emergency_relation": "Spouse",
        "health_fund": "Medibank",  "health_fund_number": "MBK100001",
    },
    {
        "title": "Ms",  "first_name": "Emily",     "last_name": "Chen",
        "preferred_name": "Em",     "dob": "22/07/1992", "gender": "Female",
        "email": "emily.chen.test02@testpatient.com.au",   "phone": "0423456789",
        "address": "45 Church Street",   "suburb": "Parramatta",   "state": "NSW", "postcode": "2150",
        "medicare": "3456789012", "medicare_ref": "1",
        "emergency_name": "David Chen",     "emergency_phone": "0423111002", "emergency_relation": "Father",
        "health_fund": "BUPA",      "health_fund_number": "BUP100002",
    },
    {
        "title": "Mrs", "first_name": "Olivia",    "last_name": "Davis",
        "preferred_name": "Olivia", "dob": "05/11/1978", "gender": "Female",
        "email": "olivia.davis.test03@testpatient.com.au", "phone": "0434567890",
        "address": "78 Hunter Street",   "suburb": "Newcastle",    "state": "NSW", "postcode": "2300",
        "medicare": "4567890123", "medicare_ref": "1",
        "emergency_name": "Peter Davis",    "emergency_phone": "0434111003", "emergency_relation": "Spouse",
        "health_fund": "HCF",       "health_fund_number": "HCF100003",
    },
    {
        "title": "Ms",  "first_name": "Sophie",    "last_name": "Martin",
        "preferred_name": "Sophie", "dob": "30/01/1995", "gender": "Female",
        "email": "sophie.martin.test04@testpatient.com.au","phone": "0445678901",
        "address": "3 Crown Street",     "suburb": "Wollongong",   "state": "NSW", "postcode": "2500",
        "medicare": "5678901234", "medicare_ref": "1",
        "emergency_name": "Anne Martin",    "emergency_phone": "0445111004", "emergency_relation": "Mother",
        "health_fund": "NIB",       "health_fund_number": "NIB100004",
    },
    {
        "title": "Mrs", "first_name": "Charlotte", "last_name": "Hill",
        "preferred_name": "Charlie","dob": "18/09/1988", "gender": "Female",
        "email": "charlotte.hill.test05@testpatient.com.au","phone": "0456789012",
        "address": "9 High Street",      "suburb": "Penrith",      "state": "NSW", "postcode": "2750",
        "medicare": "6789012345", "medicare_ref": "1",
        "emergency_name": "Tom Hill",       "emergency_phone": "0456111005", "emergency_relation": "Spouse",
        "health_fund": "AHM",       "health_fund_number": "AHM100005",
    },
    {
        "title": "Mrs", "first_name": "Ruby",      "last_name": "Nelson",
        "preferred_name": "Ruby",   "dob": "25/04/1975", "gender": "Female",
        "email": "ruby.nelson.test06@testpatient.com.au",  "phone": "0467890123",
        "address": "56 Peel Street",     "suburb": "Tamworth",     "state": "NSW", "postcode": "2340",
        "medicare": "7890123456", "medicare_ref": "1",
        "emergency_name": "John Nelson",    "emergency_phone": "0467111006", "emergency_relation": "Spouse",
        "health_fund": "Medibank",  "health_fund_number": "MBK100006",
    },
    {
        "title": "Mr",  "first_name": "William",   "last_name": "Turner",
        "preferred_name": "Will",   "dob": "07/12/1983", "gender": "Male",
        "email": "william.turner.test07@testpatient.com.au","phone": "0478901234",
        "address": "21 Jonson Street",   "suburb": "Byron Bay",    "state": "NSW", "postcode": "2481",
        "medicare": "8901234567", "medicare_ref": "1",
        "emergency_name": "Susan Turner",   "emergency_phone": "0478111007", "emergency_relation": "Spouse",
        "health_fund": "BUPA",      "health_fund_number": "BUP100007",
    },
    {
        "title": "Ms",  "first_name": "Ella",      "last_name": "Collins",
        "preferred_name": "Ella",   "dob": "14/06/2000", "gender": "Female",
        "email": "ella.collins.test08@testpatient.com.au", "phone": "0489012345",
        "address": "33 Kable Avenue",    "suburb": "Orange",       "state": "NSW", "postcode": "2800",
        "medicare": "9012345678", "medicare_ref": "1",
        "emergency_name": "Mark Collins",   "emergency_phone": "0489111008", "emergency_relation": "Father",
        "health_fund": "HCF",       "health_fund_number": "HCF100008",
    },
    {
        "title": "Mr",  "first_name": "Connor",    "last_name": "Scarlett",
        "preferred_name": "Connor", "dob": "02/08/1991", "gender": "Male",
        "email": "connor.scarlett.test09@testpatient.com.au","phone": "0491123456",
        "address": "15 Baylis Street",   "suburb": "Wagga Wagga",  "state": "NSW", "postcode": "2650",
        "medicare": "2109876549", "medicare_ref": "1",
        "emergency_name": "Lisa Scarlett",  "emergency_phone": "0491111009", "emergency_relation": "Mother",
        "health_fund": "NIB",       "health_fund_number": "NIB100009",
    },
    {
        "title": "Mr",  "first_name": "Tyler",     "last_name": "Bell",
        "preferred_name": "Ty",     "dob": "29/03/1997", "gender": "Male",
        "email": "tyler.bell.test10@testpatient.com.au",   "phone": "0412234567",
        "address": "7 Auburn Street",    "suburb": "Goulburn",     "state": "NSW", "postcode": "2580",
        "medicare": "3210987650", "medicare_ref": "1",
        "emergency_name": "Karen Bell",     "emergency_phone": "0412111010", "emergency_relation": "Mother",
        "health_fund": "AHM",       "health_fund_number": "AHM100010",
    },
    # ── VIC ──────────────────────────────────────────────────────────────────
    {
        "title": "Mr",  "first_name": "Michael",   "last_name": "O'Brien",
        "preferred_name": "Mike",   "dob": "11/05/1980", "gender": "Male",
        "email": "michael.obrien.test11@testpatient.com.au","phone": "0413345678",
        "address": "88 Collins Street",  "suburb": "Melbourne",    "state": "VIC", "postcode": "3000",
        "medicare": "4321098761", "medicare_ref": "1",
        "emergency_name": "Fiona O'Brien", "emergency_phone": "0413111011","emergency_relation": "Spouse",
        "health_fund": "Medibank",  "health_fund_number": "MBK100011",
    },
    {
        "title": "Ms",  "first_name": "Mia",       "last_name": "Lewis",
        "preferred_name": "Mia",    "dob": "19/10/1993", "gender": "Female",
        "email": "mia.lewis.test12@testpatient.com.au",    "phone": "0424456789",
        "address": "14 Bridge Road",     "suburb": "Richmond",     "state": "VIC", "postcode": "3121",
        "medicare": "5432109872", "medicare_ref": "1",
        "emergency_name": "Greg Lewis",     "emergency_phone": "0424111012","emergency_relation": "Father",
        "health_fund": "BUPA",      "health_fund_number": "BUP100012",
    },
    {
        "title": "Mr",  "first_name": "Samuel",    "last_name": "Baker",
        "preferred_name": "Sam",    "dob": "03/02/1987", "gender": "Male",
        "email": "samuel.baker.test13@testpatient.com.au", "phone": "0435567890",
        "address": "5 Moorabool Street", "suburb": "Geelong",      "state": "VIC", "postcode": "3220",
        "medicare": "6543210983", "medicare_ref": "1",
        "emergency_name": "Helen Baker",    "emergency_phone": "0435111013","emergency_relation": "Mother",
        "health_fund": "HCF",       "health_fund_number": "HCF100013",
    },
    {
        "title": "Mrs", "first_name": "Lily",      "last_name": "Green",
        "preferred_name": "Lily",   "dob": "27/08/1972", "gender": "Female",
        "email": "lily.green.test14@testpatient.com.au",   "phone": "0446678901",
        "address": "22 Sturt Street",    "suburb": "Ballarat",     "state": "VIC", "postcode": "3350",
        "medicare": "7654321094", "medicare_ref": "1",
        "emergency_name": "Bob Green",      "emergency_phone": "0446111014","emergency_relation": "Spouse",
        "health_fund": "NIB",       "health_fund_number": "NIB100014",
    },
    {
        "title": "Mr",  "first_name": "Ethan",     "last_name": "Young",
        "preferred_name": "Ethan",  "dob": "16/12/1996", "gender": "Male",
        "email": "ethan.young.test15@testpatient.com.au",  "phone": "0457789012",
        "address": "11 Mitchell Street", "suburb": "Bendigo",      "state": "VIC", "postcode": "3550",
        "medicare": "8765432105", "medicare_ref": "1",
        "emergency_name": "Sandra Young",   "emergency_phone": "0457111015","emergency_relation": "Mother",
        "health_fund": "AHM",       "health_fund_number": "AHM100015",
    },
    {
        "title": "Mr",  "first_name": "Andrew",    "last_name": "Clark",
        "preferred_name": "Andy",   "dob": "08/07/1969", "gender": "Male",
        "email": "andrew.clark.test16@testpatient.com.au", "phone": "0468890123",
        "address": "30 Commercial Road", "suburb": "Traralgon",    "state": "VIC", "postcode": "3844",
        "medicare": "9876543216", "medicare_ref": "1",
        "emergency_name": "Diane Clark",    "emergency_phone": "0468111016","emergency_relation": "Spouse",
        "health_fund": "Medibank",  "health_fund_number": "MBK100016",
    },
    {
        "title": "Ms",  "first_name": "Lucy",      "last_name": "Phillips",
        "preferred_name": "Lucy",   "dob": "21/04/1984", "gender": "Female",
        "email": "lucy.phillips.test17@testpatient.com.au","phone": "0479901234",
        "address": "6 Foot Street",      "suburb": "Warrnambool",  "state": "VIC", "postcode": "3280",
        "medicare": "2987654327", "medicare_ref": "1",
        "emergency_name": "Ian Phillips",   "emergency_phone": "0479111017","emergency_relation": "Father",
        "health_fund": "BUPA",      "health_fund_number": "BUP100017",
    },
    {
        "title": "Ms",  "first_name": "Nora",      "last_name": "Murphy",
        "preferred_name": "Nora",   "dob": "13/11/1990", "gender": "Female",
        "email": "nora.murphy.test18@testpatient.com.au",  "phone": "0490012345",
        "address": "19 Hargreaves Street","suburb": "Mildura",     "state": "VIC", "postcode": "3500",
        "medicare": "3098765438", "medicare_ref": "1",
        "emergency_name": "Sean Murphy",    "emergency_phone": "0490111018","emergency_relation": "Father",
        "health_fund": "HCF",       "health_fund_number": "HCF100018",
    },
    {
        "title": "Mr",  "first_name": "Luke",      "last_name": "Stewart",
        "preferred_name": "Luke",   "dob": "04/06/1998", "gender": "Male",
        "email": "luke.stewart.test19@testpatient.com.au", "phone": "0411123456",
        "address": "42 Lonsdale Street",  "suburb": "Dandenong",   "state": "VIC", "postcode": "3175",
        "medicare": "4109876549", "medicare_ref": "1",
        "emergency_name": "Pam Stewart",    "emergency_phone": "0411111019","emergency_relation": "Mother",
        "health_fund": "NIB",       "health_fund_number": "NIB100019",
    },
    {
        "title": "Mr",  "first_name": "Jake",      "last_name": "Rogers",
        "preferred_name": "Jake",   "dob": "31/01/1976", "gender": "Male",
        "email": "jake.rogers.test20@testpatient.com.au",  "phone": "0422234567",
        "address": "8 Albert Street",    "suburb": "Wodonga",      "state": "VIC", "postcode": "3690",
        "medicare": "5210987650", "medicare_ref": "1",
        "emergency_name": "Tina Rogers",    "emergency_phone": "0422111020","emergency_relation": "Spouse",
        "health_fund": "AHM",       "health_fund_number": "AHM100020",
    },
    # ── QLD ──────────────────────────────────────────────────────────────────
    {
        "title": "Ms",  "first_name": "Sarah",     "last_name": "Thompson",
        "preferred_name": "Sarah",  "dob": "09/09/1986", "gender": "Female",
        "email": "sarah.thompson.test21@testpatient.com.au","phone": "0433345678",
        "address": "25 Queen Street",    "suburb": "Brisbane",     "state": "QLD", "postcode": "4000",
        "medicare": "6321098761", "medicare_ref": "1",
        "emergency_name": "Paul Thompson",  "emergency_phone": "0433111021","emergency_relation": "Father",
        "health_fund": "Medibank",  "health_fund_number": "MBK100021",
    },
    {
        "title": "Ms",  "first_name": "Chloe",     "last_name": "Robinson",
        "preferred_name": "Chloe",  "dob": "17/03/1994", "gender": "Female",
        "email": "chloe.robinson.test22@testpatient.com.au","phone": "0444456789",
        "address": "77 Orchid Avenue",   "suburb": "Surfers Paradise","state": "QLD","postcode": "4217",
        "medicare": "7432109872", "medicare_ref": "1",
        "emergency_name": "Nick Robinson",  "emergency_phone": "0444111022","emergency_relation": "Father",
        "health_fund": "BUPA",      "health_fund_number": "BUP100022",
    },
    {
        "title": "Mr",  "first_name": "Nathan",    "last_name": "Allen",
        "preferred_name": "Nate",   "dob": "26/07/1982", "gender": "Male",
        "email": "nathan.allen.test23@testpatient.com.au", "phone": "0455567890",
        "address": "10 Flinders Street", "suburb": "Townsville",   "state": "QLD", "postcode": "4810",
        "medicare": "8543210983", "medicare_ref": "1",
        "emergency_name": "Kate Allen",     "emergency_phone": "0455111023","emergency_relation": "Spouse",
        "health_fund": "HCF",       "health_fund_number": "HCF100023",
    },
    {
        "title": "Mrs", "first_name": "Hannah",    "last_name": "Mitchell",
        "preferred_name": "Hannah", "dob": "01/12/1970", "gender": "Female",
        "email": "hannah.mitchell.test24@testpatient.com.au","phone": "0466678901",
        "address": "38 Shield Street",   "suburb": "Cairns",       "state": "QLD", "postcode": "4870",
        "medicare": "9654321094", "medicare_ref": "1",
        "emergency_name": "Rick Mitchell",  "emergency_phone": "0466111024","emergency_relation": "Spouse",
        "health_fund": "NIB",       "health_fund_number": "NIB100024",
    },
    {
        "title": "Mr",  "first_name": "Thomas",    "last_name": "Campbell",
        "preferred_name": "Tom",    "dob": "23/05/1999", "gender": "Male",
        "email": "thomas.campbell.test25@testpatient.com.au","phone": "0477789012",
        "address": "52 Ruthven Street",  "suburb": "Toowoomba",    "state": "QLD", "postcode": "4350",
        "medicare": "2765432105", "medicare_ref": "1",
        "emergency_name": "Mary Campbell",  "emergency_phone": "0477111025","emergency_relation": "Mother",
        "health_fund": "AHM",       "health_fund_number": "AHM100025",
    },
    {
        "title": "Ms",  "first_name": "Amelia",    "last_name": "Parker",
        "preferred_name": "Amy",    "dob": "10/08/1989", "gender": "Female",
        "email": "amelia.parker.test26@testpatient.com.au","phone": "0488890123",
        "address": "16 Bayview Street",  "suburb": "Hervey Bay",   "state": "QLD", "postcode": "4655",
        "medicare": "3876543216", "medicare_ref": "1",
        "emergency_name": "Bruce Parker",   "emergency_phone": "0488111026","emergency_relation": "Father",
        "health_fund": "Medibank",  "health_fund_number": "MBK100026",
    },
    {
        "title": "Ms",  "first_name": "Aria",      "last_name": "Morris",
        "preferred_name": "Aria",   "dob": "06/02/1995", "gender": "Female",
        "email": "aria.morris.test27@testpatient.com.au",  "phone": "0499901234",
        "address": "29 Nebo Road",       "suburb": "Mackay",       "state": "QLD", "postcode": "4740",
        "medicare": "4987654327", "medicare_ref": "1",
        "emergency_name": "Gary Morris",    "emergency_phone": "0499111027","emergency_relation": "Father",
        "health_fund": "BUPA",      "health_fund_number": "BUP100027",
    },
    {
        "title": "Mr",  "first_name": "Dylan",     "last_name": "Cook",
        "preferred_name": "Dyl",    "dob": "15/10/1977", "gender": "Male",
        "email": "dylan.cook.test28@testpatient.com.au",   "phone": "0410012345",
        "address": "4 Bourbong Street",  "suburb": "Bundaberg",    "state": "QLD", "postcode": "4670",
        "medicare": "5098765438", "medicare_ref": "1",
        "emergency_name": "Val Cook",       "emergency_phone": "0410111028","emergency_relation": "Spouse",
        "health_fund": "HCF",       "health_fund_number": "HCF100028",
    },
    {
        "title": "Mr",  "first_name": "Liam",      "last_name": "Bailey",
        "preferred_name": "Liam",   "dob": "28/04/2001", "gender": "Male",
        "email": "liam.bailey.test29@testpatient.com.au",  "phone": "0421123456",
        "address": "63 Goondoon Street", "suburb": "Gladstone",    "state": "QLD", "postcode": "4680",
        "medicare": "6109876549", "medicare_ref": "1",
        "emergency_name": "Jenny Bailey",   "emergency_phone": "0421111029","emergency_relation": "Mother",
        "health_fund": "NIB",       "health_fund_number": "NIB100029",
    },
    {
        "title": "Ms",  "first_name": "Ellie",     "last_name": "Rivera",
        "preferred_name": "Ellie",  "dob": "12/06/1985", "gender": "Female",
        "email": "ellie.rivera.test30@testpatient.com.au", "phone": "0432234567",
        "address": "18 East Street",     "suburb": "Rockhampton",  "state": "QLD", "postcode": "4700",
        "medicare": "7210987650", "medicare_ref": "1",
        "emergency_name": "Carlos Rivera",  "emergency_phone": "0432111030","emergency_relation": "Father",
        "health_fund": "AHM",       "health_fund_number": "AHM100030",
    },
    # ── WA ───────────────────────────────────────────────────────────────────
    {
        "title": "Mr",  "first_name": "Robert",    "last_name": "Taylor",
        "preferred_name": "Rob",    "dob": "20/01/1973", "gender": "Male",
        "email": "robert.taylor.test31@testpatient.com.au","phone": "0443345678",
        "address": "100 St Georges Terrace","suburb": "Perth",     "state": "WA",  "postcode": "6000",
        "medicare": "8321098761", "medicare_ref": "1",
        "emergency_name": "Linda Taylor",   "emergency_phone": "0443111031","emergency_relation": "Spouse",
        "health_fund": "HBF",       "health_fund_number": "HBF100031",
    },
    {
        "title": "Ms",  "first_name": "Grace",     "last_name": "Hall",
        "preferred_name": "Grace",  "dob": "08/09/1991", "gender": "Female",
        "email": "grace.hall.test32@testpatient.com.au",   "phone": "0454456789",
        "address": "31 High Street",     "suburb": "Fremantle",    "state": "WA",  "postcode": "6160",
        "medicare": "9432109872", "medicare_ref": "1",
        "emergency_name": "Tom Hall",       "emergency_phone": "0454111032","emergency_relation": "Father",
        "health_fund": "HBF",       "health_fund_number": "HBF100032",
    },
    {
        "title": "Ms",  "first_name": "Ava",       "last_name": "Scott",
        "preferred_name": "Ava",    "dob": "24/03/1997", "gender": "Female",
        "email": "ava.scott.test33@testpatient.com.au",    "phone": "0465567890",
        "address": "7 Victoria Street",  "suburb": "Bunbury",      "state": "WA",  "postcode": "6230",
        "medicare": "2543210983", "medicare_ref": "1",
        "emergency_name": "Lyn Scott",      "emergency_phone": "0465111033","emergency_relation": "Mother",
        "health_fund": "Medibank",  "health_fund_number": "MBK100033",
    },
    {
        "title": "Mr",  "first_name": "Alexander", "last_name": "Adams",
        "preferred_name": "Alex",   "dob": "16/11/1981", "gender": "Male",
        "email": "alexander.adams.test34@testpatient.com.au","phone": "0476678901",
        "address": "44 Marine Terrace",  "suburb": "Geraldton",    "state": "WA",  "postcode": "6530",
        "medicare": "3654321094", "medicare_ref": "1",
        "emergency_name": "Rachel Adams",   "emergency_phone": "0476111034","emergency_relation": "Spouse",
        "health_fund": "BUPA",      "health_fund_number": "BUP100034",
    },
    {
        "title": "Ms",  "first_name": "Zoe",       "last_name": "Roberts",
        "preferred_name": "Zoe",    "dob": "03/07/1988", "gender": "Female",
        "email": "zoe.roberts.test35@testpatient.com.au",  "phone": "0487789012",
        "address": "19 Stirling Street", "suburb": "Northam",      "state": "WA",  "postcode": "6401",
        "medicare": "4765432105", "medicare_ref": "1",
        "emergency_name": "Neil Roberts",   "emergency_phone": "0487111035","emergency_relation": "Father",
        "health_fund": "HCF",       "health_fund_number": "HCF100035",
    },
    {
        "title": "Mr",  "first_name": "Ryan",      "last_name": "Evans",
        "preferred_name": "Ryan",   "dob": "11/04/1966", "gender": "Male",
        "email": "ryan.evans.test36@testpatient.com.au",   "phone": "0498890123",
        "address": "6 Wittenoom Street", "suburb": "Albany",       "state": "WA",  "postcode": "6330",
        "medicare": "5876543216", "medicare_ref": "1",
        "emergency_name": "Carol Evans",    "emergency_phone": "0498111036","emergency_relation": "Spouse",
        "health_fund": "NIB",       "health_fund_number": "NIB100036",
    },
    {
        "title": "Ms",  "first_name": "Hazel",     "last_name": "Morgan",
        "preferred_name": "Hazel",  "dob": "29/08/2002", "gender": "Female",
        "email": "hazel.morgan.test37@testpatient.com.au", "phone": "0409901234",
        "address": "55 Chamberlain Street","suburb": "Kalgoorlie", "state": "WA",  "postcode": "6430",
        "medicare": "6987654327", "medicare_ref": "1",
        "emergency_name": "Pat Morgan",     "emergency_phone": "0409111037","emergency_relation": "Mother",
        "health_fund": "HBF",       "health_fund_number": "HBF100037",
    },
    {
        "title": "Mr",  "first_name": "Joshua",    "last_name": "Walker",
        "preferred_name": "Josh",   "dob": "07/02/1979", "gender": "Male",
        "email": "joshua.walker.test38@testpatient.com.au","phone": "0420012345",
        "address": "12 Durlacher Street","suburb": "Geraldton",    "state": "WA",  "postcode": "6530",
        "medicare": "7098765438", "medicare_ref": "1",
        "emergency_name": "Sue Walker",     "emergency_phone": "0420111038","emergency_relation": "Spouse",
        "health_fund": "AHM",       "health_fund_number": "AHM100038",
    },
    # ── SA ───────────────────────────────────────────────────────────────────
    {
        "title": "Ms",  "first_name": "Jessica",   "last_name": "Brown",
        "preferred_name": "Jess",   "dob": "15/06/1990", "gender": "Female",
        "email": "jessica.brown.test39@testpatient.com.au","phone": "0431123456",
        "address": "72 King William Street","suburb": "Adelaide",  "state": "SA",  "postcode": "5000",
        "medicare": "8109876549", "medicare_ref": "1",
        "emergency_name": "Dan Brown",      "emergency_phone": "0431111039","emergency_relation": "Father",
        "health_fund": "Medibank",  "health_fund_number": "MBK100039",
    },
    {
        "title": "Mr",  "first_name": "Benjamin",  "last_name": "King",
        "preferred_name": "Ben",    "dob": "23/10/1983", "gender": "Male",
        "email": "benjamin.king.test40@testpatient.com.au","phone": "0442234567",
        "address": "9 Moseley Street",   "suburb": "Glenelg",      "state": "SA",  "postcode": "5045",
        "medicare": "9210987650", "medicare_ref": "1",
        "emergency_name": "Angela King",    "emergency_phone": "0442111040","emergency_relation": "Spouse",
        "health_fund": "BUPA",      "health_fund_number": "BUP100040",
    },
    {
        "title": "Mr",  "first_name": "Jack",      "last_name": "Perez",
        "preferred_name": "Jack",   "dob": "01/05/1974", "gender": "Male",
        "email": "jack.perez.test41@testpatient.com.au",   "phone": "0453345678",
        "address": "34 Commercial Road", "suburb": "Port Adelaide", "state": "SA",  "postcode": "5015",
        "medicare": "2321098761", "medicare_ref": "1",
        "emergency_name": "Maria Perez",    "emergency_phone": "0453111041","emergency_relation": "Spouse",
        "health_fund": "HCF",       "health_fund_number": "HCF100041",
    },
    {
        "title": "Ms",  "first_name": "Violet",    "last_name": "Reed",
        "preferred_name": "Vi",     "dob": "18/12/1998", "gender": "Female",
        "email": "violet.reed.test42@testpatient.com.au",  "phone": "0464456789",
        "address": "22 Commercial Street","suburb": "Mount Gambier","state": "SA", "postcode": "5290",
        "medicare": "3432109872", "medicare_ref": "1",
        "emergency_name": "Owen Reed",      "emergency_phone": "0464111042","emergency_relation": "Father",
        "health_fund": "NIB",       "health_fund_number": "NIB100042",
    },
    {
        "title": "Ms",  "first_name": "Scarlett",  "last_name": "Morris",
        "preferred_name": "Scar",   "dob": "09/07/1986", "gender": "Female",
        "email": "scarlett.morris.test43@testpatient.com.au","phone": "0475567890",
        "address": "5 Wright Road",      "suburb": "Whyalla",      "state": "SA",  "postcode": "5600",
        "medicare": "4543210983", "medicare_ref": "1",
        "emergency_name": "Kevin Morris",   "emergency_phone": "0475111043","emergency_relation": "Spouse",
        "health_fund": "AHM",       "health_fund_number": "AHM100043",
    },
    # ── TAS ──────────────────────────────────────────────────────────────────
    {
        "title": "Mrs", "first_name": "Isabella",  "last_name": "White",
        "preferred_name": "Bella",  "dob": "27/03/1993", "gender": "Female",
        "email": "isabella.white.test44@testpatient.com.au","phone": "0486678901",
        "address": "66 Liverpool Street","suburb": "Hobart",       "state": "TAS", "postcode": "7000",
        "medicare": "5654321094", "medicare_ref": "1",
        "emergency_name": "Chris White",    "emergency_phone": "0486111044","emergency_relation": "Spouse",
        "health_fund": "Medibank",  "health_fund_number": "MBK100044",
    },
    {
        "title": "Mr",  "first_name": "Lachlan",   "last_name": "Hughes",
        "preferred_name": "Lach",   "dob": "14/09/1971", "gender": "Male",
        "email": "lachlan.hughes.test45@testpatient.com.au","phone": "0497789012",
        "address": "31 St John Street",  "suburb": "Launceston",   "state": "TAS", "postcode": "7250",
        "medicare": "6765432105", "medicare_ref": "1",
        "emergency_name": "Wendy Hughes",   "emergency_phone": "0497111045","emergency_relation": "Spouse",
        "health_fund": "BUPA",      "health_fund_number": "BUP100045",
    },
    {
        "title": "Ms",  "first_name": "Zara",      "last_name": "Price",
        "preferred_name": "Zara",   "dob": "06/01/2003", "gender": "Female",
        "email": "zara.price.test46@testpatient.com.au",   "phone": "0408890123",
        "address": "8 Forbes Street",    "suburb": "Devonport",    "state": "TAS", "postcode": "7310",
        "medicare": "7876543216", "medicare_ref": "1",
        "emergency_name": "Fran Price",     "emergency_phone": "0408111046","emergency_relation": "Mother",
        "health_fund": "HCF",       "health_fund_number": "HCF100046",
    },
    # ── ACT ──────────────────────────────────────────────────────────────────
    {
        "title": "Mr",  "first_name": "Daniel",    "last_name": "Harris",
        "preferred_name": "Dan",    "dob": "20/08/1987", "gender": "Male",
        "email": "daniel.harris.test47@testpatient.com.au","phone": "0419901234",
        "address": "17 Garema Place",    "suburb": "Canberra",     "state": "ACT", "postcode": "2601",
        "medicare": "8987654327", "medicare_ref": "1",
        "emergency_name": "Kim Harris",     "emergency_phone": "0419111047","emergency_relation": "Spouse",
        "health_fund": "NIB",       "health_fund_number": "NIB100047",
    },
    {
        "title": "Ms",  "first_name": "Freya",     "last_name": "Bennett",
        "preferred_name": "Freya",  "dob": "11/04/1994", "gender": "Female",
        "email": "freya.bennett.test48@testpatient.com.au","phone": "0430012345",
        "address": "3 Woolley Street",   "suburb": "Dickson",      "state": "ACT", "postcode": "2602",
        "medicare": "9098765438", "medicare_ref": "1",
        "emergency_name": "Alan Bennett",   "emergency_phone": "0430111048","emergency_relation": "Father",
        "health_fund": "AHM",       "health_fund_number": "AHM100048",
    },
    # ── NT ───────────────────────────────────────────────────────────────────
    {
        "title": "Mr",  "first_name": "Marcus",    "last_name": "Sullivan",
        "preferred_name": "Marc",   "dob": "25/11/1980", "gender": "Male",
        "email": "marcus.sullivan.test49@testpatient.com.au","phone": "0441123456",
        "address": "48 Smith Street",    "suburb": "Darwin",       "state": "NT",  "postcode": "0800",
        "medicare": "2109876519", "medicare_ref": "1",
        "emergency_name": "Gail Sullivan",  "emergency_phone": "0441111049","emergency_relation": "Spouse",
        "health_fund": "Medibank",  "health_fund_number": "MBK100049",
    },
    {
        "title": "Mrs", "first_name": "Penelope",  "last_name": "Walsh",
        "preferred_name": "Penny",  "dob": "17/06/1976", "gender": "Female",
        "email": "penelope.walsh.test50@testpatient.com.au","phone": "0452234567",
        "address": "12 Todd Street",     "suburb": "Alice Springs", "state": "NT",  "postcode": "0870",
        "medicare": "3210987620", "medicare_ref": "1",
        "emergency_name": "Steve Walsh",    "emergency_phone": "0452111050","emergency_relation": "Spouse",
        "health_fund": "BUPA",      "health_fund_number": "BUP100050",
    },
]

# ── Selenium helpers ──────────────────────────────────────────────────────────

def wait_for_react(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script(
            "const r = document.getElementById('root'); return r && r.children.length > 0;"
        )
    )


def safe_fill(wait, driver, label_texts, value, timeout=6):
    """Try multiple XPath strategies to locate and fill an input field."""
    xpaths = []
    for label in label_texts:
        slug  = label.lower().replace(" ", "")
        slugu = label.lower().replace(" ", "_")
        xpaths += [
            # Standard <label> association
            f"//input[@id=//label[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{label.lower()}')]/@for]",
            # aria-label
            f"//input[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{label.lower()}')]",
            # placeholder
            f"//input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{label.lower()}')]",
            # name attribute
            f"//input[contains(@name,'{slug}')]",
            f"//input[contains(@name,'{slugu}')]",
            # id attribute
            f"//input[contains(@id,'{slug}')]",
            f"//input[contains(@id,'{slugu}')]",
        ]
    for xpath in xpaths:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.clear()
            el.send_keys(value)
            return True
        except Exception:
            continue
    return False


def safe_select(wait, driver, label_texts, value, timeout=5):
    """Try to select a <select> dropdown or click a custom option."""
    for label in label_texts:
        slug  = label.lower().replace(" ", "")
        slugu = label.lower().replace(" ", "_")
        xpaths = [
            f"//select[@id=//label[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{label.lower()}')]/@for]",
            f"//select[contains(@name,'{slug}')]",
            f"//select[contains(@name,'{slugu}')]",
            f"//select[contains(@id,'{slug}')]",
        ]
        for xpath in xpaths:
            try:
                el = WebDriverWait(driver, timeout).until(
                    EC.visibility_of_element_located((By.XPATH, xpath))
                )
                Select(el).select_by_visible_text(value)
                return True
            except Exception:
                continue
        # Custom dropdown: click trigger → pick option
        try:
            trigger_xpath = f"//*[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{label.lower()}')]"
            trigger = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, trigger_xpath))
            )
            trigger.click()
            time.sleep(0.4)
            option = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[@role='option' and normalize-space(.)='{value}']"))
            )
            option.click()
            return True
        except Exception:
            continue
    # Last resort: visible text click (radio buttons)
    try:
        el = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text())='{value}']"))
        )
        el.click()
        return True
    except Exception:
        pass
    return False


def click_button(driver, *labels, timeout=5):
    """Click the first matching button or link by visible text."""
    for label in labels:
        xpaths = [
            f"//button[contains(normalize-space(.),'{label}')]",
            f"//a[contains(normalize-space(.),'{label}')]",
            f"//*[@role='button' and contains(normalize-space(.),'{label}')]",
        ]
        for xpath in xpaths:
            try:
                el = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                time.sleep(0.2)
                el.click()
                return label
            except Exception:
                continue
    return None


# ── Per-patient registration ──────────────────────────────────────────────────

def register_patient(driver, wait, p, idx, total):
    tag    = f"[{idx:02d}/{total}]"
    result = {
        "index":  idx,
        "name":   f"{p['first_name']} {p['last_name']}",
        "email":  p["email"],
        "state":  p["state"],
        "dob":    p["dob"],
        "gender": p["gender"],
        "phone":  p["phone"],
        "address":f"{p['address']}, {p['suburb']} {p['state']} {p['postcode']}",
        "medicare": p["medicare"],
        "health_fund": p["health_fund"],
        "status": "FAIL",
        "detail": "",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        print(f"\n{tag} {p['first_name']} {p['last_name']} ({p['state']}) ...")

        driver.get(URL)
        wait_for_react(driver)

        # ── Click Create an account ───────────────────────────────────────────
        clicked = click_button(driver,
            "Create an account", "Create Account", "Register",
            "Sign up", "New patient", "Create patient",
            timeout=8,
        )
        if not clicked:
            result["detail"] = "Create an account button not found"
            return result

        time.sleep(1.5)

        # ── Personal details ──────────────────────────────────────────────────
        safe_select(wait, driver, ["Title", "Salutation"],           p["title"])
        safe_fill(wait, driver,   ["First name", "Given name"],      p["first_name"])
        safe_fill(wait, driver,   ["Last name", "Surname", "Family name"], p["last_name"])
        safe_fill(wait, driver,   ["Preferred name", "Preferred"],   p["preferred_name"])
        safe_fill(wait, driver,   ["Date of birth", "DOB", "Birthday"], p["dob"])
        safe_select(wait, driver, ["Gender", "Sex"],                  p["gender"])

        # ── Contact ───────────────────────────────────────────────────────────
        safe_fill(wait, driver, ["Email", "Email address"],          p["email"])
        safe_fill(wait, driver, ["Password"],                        PASSWORD)
        safe_fill(wait, driver, ["Confirm password", "Confirm"],     PASSWORD)
        safe_fill(wait, driver, ["Mobile", "Mobile number", "Phone","Phone number"], p["phone"])

        # ── Address ───────────────────────────────────────────────────────────
        safe_fill(wait, driver, ["Address", "Street address", "Address line 1"], p["address"])
        safe_fill(wait, driver, ["Suburb", "City", "Town"],          p["suburb"])
        safe_select(wait, driver,["State", "State/Territory"],        p["state"])
        safe_fill(wait, driver, ["Postcode", "Post code", "Zip"],    p["postcode"])

        # ── Medicare ──────────────────────────────────────────────────────────
        safe_fill(wait, driver, ["Medicare", "Medicare number", "Medicare card number"], p["medicare"])
        safe_fill(wait, driver, ["Medicare reference", "Reference number", "IRN"],       p["medicare_ref"])

        # ── Emergency contact ─────────────────────────────────────────────────
        safe_fill(wait, driver, ["Emergency contact", "Emergency contact name", "Next of kin"], p["emergency_name"])
        safe_fill(wait, driver, ["Emergency phone", "Emergency contact phone"],                  p["emergency_phone"])
        safe_fill(wait, driver, ["Relationship"],                                                p["emergency_relation"])
        safe_select(wait, driver,["Relationship"],                                               p["emergency_relation"])

        # ── Health fund ───────────────────────────────────────────────────────
        safe_select(wait, driver,["Health fund", "Private health"],                  p["health_fund"])
        safe_fill(wait, driver,  ["Health fund", "Private health"],                  p["health_fund"])
        safe_fill(wait, driver,  ["Health fund number", "Member number", "Membership number"], p["health_fund_number"])

        # ── Handle paginated forms (click Next up to 5 times) ─────────────────
        for _ in range(5):
            nxt = click_button(driver, "Next", "Continue", timeout=2)
            if not nxt:
                break
            time.sleep(0.8)

        # ── Submit ────────────────────────────────────────────────────────────
        submitted = click_button(driver,
            "Register", "Create account", "Create patient",
            "Sign up", "Submit", "Save", "Confirm",
            timeout=5,
        )
        if not submitted:
            shot = os.path.join(SCREENSHOT_DIR, f"patient_{idx:02d}_no_submit.png")
            driver.save_screenshot(shot)
            result["detail"] = f"Submit button not found — see {shot}"
            return result

        time.sleep(3)

        shot = os.path.join(SCREENSHOT_DIR, f"patient_{idx:02d}_result.png")
        driver.save_screenshot(shot)

        body = driver.find_element(By.TAG_NAME, "body").text.lower()
        errors = ["error", "invalid", "already exists", "already registered", "failed", "required"]
        if any(e in body for e in errors):
            result["status"] = "WARN"
            result["detail"] = f"Possible error after submit — URL: {driver.current_url}"
        else:
            result["status"] = "OK"
            result["detail"] = f"OK — {driver.current_url}"

        print(f"      {result['status']} → {result['detail'][:80]}")

    except Exception as exc:
        result["detail"] = str(exc)[:300]
        print(f"      FAIL: {result['detail']}")
        try:
            shot = os.path.join(SCREENSHOT_DIR, f"patient_{idx:02d}_error.png")
            driver.save_screenshot(shot)
        except Exception:
            pass

    return result


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    options = Options()
    # options.add_argument("--headless=new")   # uncomment for headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    wait  = WebDriverWait(driver, 15)
    total = len(PATIENTS)
    start = datetime.now()

    print(f"\n{'='*65}")
    print(f"  OzMed — Registering {total} Australian patients (Selenium)")
    print(f"  Target : {URL}")
    print(f"  Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}")

    results = []
    try:
        for idx, patient in enumerate(PATIENTS, start=1):
            r = register_patient(driver, wait, patient, idx, total)
            results.append(r)
            time.sleep(1.5)
    finally:
        driver.quit()

    # ── Save CSV ──────────────────────────────────────────────────────────────
    csv_fields = ["index", "name", "email", "state", "dob", "gender",
                  "phone", "address", "medicare", "health_fund",
                  "status", "detail", "timestamp"]
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    # ── Save JSON ─────────────────────────────────────────────────────────────
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    ok   = sum(1 for r in results if r["status"] == "OK")
    warn = sum(1 for r in results if r["status"] == "WARN")
    fail = sum(1 for r in results if r["status"] == "FAIL")
    secs = int((datetime.now() - start).total_seconds())

    print(f"\n{'='*65}")
    print(f"  Done in {secs}s")
    print(f"  OK: {ok}  |  WARN: {warn}  |  FAIL: {fail}  |  Total: {total}")
    print(f"  CSV        → {RESULTS_CSV}")
    print(f"  JSON       → {RESULTS_JSON}")
    print(f"  Screenshots→ {SCREENSHOT_DIR}/")
    print(f"{'='*65}\n")

    if fail or warn:
        print("  Patients with issues:")
        for r in results:
            if r["status"] != "OK":
                print(f"    [{r['index']:02d}] {r['name']:25s} {r['status']} — {r['detail'][:60]}")


if __name__ == "__main__":
    main()
