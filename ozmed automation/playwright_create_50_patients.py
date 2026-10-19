"""
Playwright script — OzMed Create 50 Australian Patients
Target: https://practice2.dev.ozmed.health/

Loops through 50 realistic Australian patient records and registers each one,
covering all states/territories with proper Australian health data (Medicare,
emergency contacts, health fund, DOB, gender, address).

Install:
    pip install playwright
    playwright install chromium

Run:
    python playwright_create_50_patients.py
"""

import asyncio
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

URL            = "https://practice2.dev.ozmed.health/"
SCREENSHOT_DIR = "patient_screenshots"
RESULTS_CSV    = "patient_results.csv"
PASSWORD       = "Test@Patient2024!"

# ── 50 Australian patients ────────────────────────────────────────────────────
# Fields: first_name, last_name, preferred_name, title, dob, gender, email,
#         phone, address, suburb, state, postcode, medicare, medicare_ref,
#         emergency_name, emergency_phone, emergency_relation,
#         health_fund, health_fund_number
PATIENTS = [
    # ── NSW ──────────────────────────────────────────────────────────────────
    {
        "title": "Mr",   "first_name": "James",      "last_name": "Wilson",
        "preferred_name": "James",   "dob": "14/03/1985",  "gender": "Male",
        "email": "james.wilson.test01@testpatient.com.au",  "phone": "0412 345 678",
        "address": "12 Harbour Street", "suburb": "Sydney",      "state": "NSW", "postcode": "2000",
        "medicare": "2345 67890 1",  "medicare_ref": "1",
        "emergency_name": "Claire Wilson",  "emergency_phone": "0412 111 001",  "emergency_relation": "Spouse",
        "health_fund": "Medibank",   "health_fund_number": "MBK100001",
    },
    {
        "title": "Ms",   "first_name": "Emily",      "last_name": "Chen",
        "preferred_name": "Em",      "dob": "22/07/1992",  "gender": "Female",
        "email": "emily.chen.test02@testpatient.com.au",    "phone": "0423 456 789",
        "address": "45 Church Street",   "suburb": "Parramatta",  "state": "NSW", "postcode": "2150",
        "medicare": "3456 78901 2",  "medicare_ref": "1",
        "emergency_name": "David Chen",     "emergency_phone": "0423 111 002",  "emergency_relation": "Father",
        "health_fund": "BUPA",       "health_fund_number": "BUP100002",
    },
    {
        "title": "Mrs",  "first_name": "Olivia",     "last_name": "Davis",
        "preferred_name": "Olivia",  "dob": "05/11/1978",  "gender": "Female",
        "email": "olivia.davis.test03@testpatient.com.au",  "phone": "0434 567 890",
        "address": "78 Hunter Street",   "suburb": "Newcastle",   "state": "NSW", "postcode": "2300",
        "medicare": "4567 89012 3",  "medicare_ref": "1",
        "emergency_name": "Peter Davis",    "emergency_phone": "0434 111 003",  "emergency_relation": "Spouse",
        "health_fund": "HCF",        "health_fund_number": "HCF100003",
    },
    {
        "title": "Ms",   "first_name": "Sophie",     "last_name": "Martin",
        "preferred_name": "Sophie",  "dob": "30/01/1995",  "gender": "Female",
        "email": "sophie.martin.test04@testpatient.com.au", "phone": "0445 678 901",
        "address": "3 Crown Street",     "suburb": "Wollongong",  "state": "NSW", "postcode": "2500",
        "medicare": "5678 90123 4",  "medicare_ref": "1",
        "emergency_name": "Anne Martin",    "emergency_phone": "0445 111 004",  "emergency_relation": "Mother",
        "health_fund": "NIB",        "health_fund_number": "NIB100004",
    },
    {
        "title": "Mrs",  "first_name": "Charlotte",  "last_name": "Hill",
        "preferred_name": "Charlie", "dob": "18/09/1988",  "gender": "Female",
        "email": "charlotte.hill.test05@testpatient.com.au","phone": "0456 789 012",
        "address": "9 High Street",      "suburb": "Penrith",     "state": "NSW", "postcode": "2750",
        "medicare": "6789 01234 5",  "medicare_ref": "1",
        "emergency_name": "Tom Hill",       "emergency_phone": "0456 111 005",  "emergency_relation": "Spouse",
        "health_fund": "AHM",        "health_fund_number": "AHM100005",
    },
    {
        "title": "Mrs",  "first_name": "Ruby",       "last_name": "Nelson",
        "preferred_name": "Ruby",    "dob": "25/04/1975",  "gender": "Female",
        "email": "ruby.nelson.test06@testpatient.com.au",   "phone": "0467 890 123",
        "address": "56 Peel Street",     "suburb": "Tamworth",    "state": "NSW", "postcode": "2340",
        "medicare": "7890 12345 6",  "medicare_ref": "1",
        "emergency_name": "John Nelson",    "emergency_phone": "0467 111 006",  "emergency_relation": "Spouse",
        "health_fund": "Medibank",   "health_fund_number": "MBK100006",
    },
    {
        "title": "Mr",   "first_name": "William",    "last_name": "Turner",
        "preferred_name": "Will",    "dob": "07/12/1983",  "gender": "Male",
        "email": "william.turner.test07@testpatient.com.au","phone": "0478 901 234",
        "address": "21 Jonson Street",   "suburb": "Byron Bay",   "state": "NSW", "postcode": "2481",
        "medicare": "8901 23456 7",  "medicare_ref": "1",
        "emergency_name": "Susan Turner",   "emergency_phone": "0478 111 007",  "emergency_relation": "Spouse",
        "health_fund": "BUPA",       "health_fund_number": "BUP100007",
    },
    {
        "title": "Ms",   "first_name": "Ella",       "last_name": "Collins",
        "preferred_name": "Ella",    "dob": "14/06/2000",  "gender": "Female",
        "email": "ella.collins.test08@testpatient.com.au",  "phone": "0489 012 345",
        "address": "33 Kable Avenue",    "suburb": "Orange",      "state": "NSW", "postcode": "2800",
        "medicare": "9012 34567 8",  "medicare_ref": "1",
        "emergency_name": "Mark Collins",   "emergency_phone": "0489 111 008",  "emergency_relation": "Father",
        "health_fund": "HCF",        "health_fund_number": "HCF100008",
    },
    {
        "title": "Mr",   "first_name": "Connor",     "last_name": "Scarlett",
        "preferred_name": "Connor",  "dob": "02/08/1991",  "gender": "Male",
        "email": "connor.scarlett.test09@testpatient.com.au","phone": "0491 123 456",
        "address": "15 Baylis Street",   "suburb": "Wagga Wagga", "state": "NSW", "postcode": "2650",
        "medicare": "2109 87654 9",  "medicare_ref": "1",
        "emergency_name": "Lisa Scarlett",  "emergency_phone": "0491 111 009",  "emergency_relation": "Mother",
        "health_fund": "NIB",        "health_fund_number": "NIB100009",
    },
    {
        "title": "Mr",   "first_name": "Tyler",      "last_name": "Bell",
        "preferred_name": "Ty",      "dob": "29/03/1997",  "gender": "Male",
        "email": "tyler.bell.test10@testpatient.com.au",    "phone": "0412 234 567",
        "address": "7 Auburn Street",    "suburb": "Goulburn",    "state": "NSW", "postcode": "2580",
        "medicare": "3210 98765 0",  "medicare_ref": "1",
        "emergency_name": "Karen Bell",     "emergency_phone": "0412 111 010",  "emergency_relation": "Mother",
        "health_fund": "AHM",        "health_fund_number": "AHM100010",
    },
    # ── VIC ──────────────────────────────────────────────────────────────────
    {
        "title": "Mr",   "first_name": "Michael",    "last_name": "O'Brien",
        "preferred_name": "Mike",    "dob": "11/05/1980",  "gender": "Male",
        "email": "michael.obrien.test11@testpatient.com.au","phone": "0413 345 678",
        "address": "88 Collins Street",  "suburb": "Melbourne",   "state": "VIC", "postcode": "3000",
        "medicare": "4321 09876 1",  "medicare_ref": "1",
        "emergency_name": "Fiona O'Brien", "emergency_phone": "0413 111 011",  "emergency_relation": "Spouse",
        "health_fund": "Medibank",   "health_fund_number": "MBK100011",
    },
    {
        "title": "Ms",   "first_name": "Mia",        "last_name": "Lewis",
        "preferred_name": "Mia",     "dob": "19/10/1993",  "gender": "Female",
        "email": "mia.lewis.test12@testpatient.com.au",     "phone": "0424 456 789",
        "address": "14 Bridge Road",     "suburb": "Richmond",    "state": "VIC", "postcode": "3121",
        "medicare": "5432 10987 2",  "medicare_ref": "1",
        "emergency_name": "Greg Lewis",     "emergency_phone": "0424 111 012",  "emergency_relation": "Father",
        "health_fund": "BUPA",       "health_fund_number": "BUP100012",
    },
    {
        "title": "Mr",   "first_name": "Samuel",     "last_name": "Baker",
        "preferred_name": "Sam",     "dob": "03/02/1987",  "gender": "Male",
        "email": "samuel.baker.test13@testpatient.com.au",  "phone": "0435 567 890",
        "address": "5 Moorabool Street", "suburb": "Geelong",     "state": "VIC", "postcode": "3220",
        "medicare": "6543 21098 3",  "medicare_ref": "1",
        "emergency_name": "Helen Baker",    "emergency_phone": "0435 111 013",  "emergency_relation": "Mother",
        "health_fund": "HCF",        "health_fund_number": "HCF100013",
    },
    {
        "title": "Mrs",  "first_name": "Lily",       "last_name": "Green",
        "preferred_name": "Lily",    "dob": "27/08/1972",  "gender": "Female",
        "email": "lily.green.test14@testpatient.com.au",    "phone": "0446 678 901",
        "address": "22 Sturt Street",    "suburb": "Ballarat",    "state": "VIC", "postcode": "3350",
        "medicare": "7654 32109 4",  "medicare_ref": "1",
        "emergency_name": "Bob Green",      "emergency_phone": "0446 111 014",  "emergency_relation": "Spouse",
        "health_fund": "NIB",        "health_fund_number": "NIB100014",
    },
    {
        "title": "Mr",   "first_name": "Ethan",      "last_name": "Young",
        "preferred_name": "Ethan",   "dob": "16/12/1996",  "gender": "Male",
        "email": "ethan.young.test15@testpatient.com.au",   "phone": "0457 789 012",
        "address": "11 Mitchell Street", "suburb": "Bendigo",     "state": "VIC", "postcode": "3550",
        "medicare": "8765 43210 5",  "medicare_ref": "1",
        "emergency_name": "Sandra Young",   "emergency_phone": "0457 111 015",  "emergency_relation": "Mother",
        "health_fund": "AHM",        "health_fund_number": "AHM100015",
    },
    {
        "title": "Mr",   "first_name": "Andrew",     "last_name": "Clark",
        "preferred_name": "Andy",    "dob": "08/07/1969",  "gender": "Male",
        "email": "andrew.clark.test16@testpatient.com.au",  "phone": "0468 890 123",
        "address": "30 Commercial Road", "suburb": "Traralgon",   "state": "VIC", "postcode": "3844",
        "medicare": "9876 54321 6",  "medicare_ref": "1",
        "emergency_name": "Diane Clark",    "emergency_phone": "0468 111 016",  "emergency_relation": "Spouse",
        "health_fund": "Medibank",   "health_fund_number": "MBK100016",
    },
    {
        "title": "Ms",   "first_name": "Lucy",       "last_name": "Phillips",
        "preferred_name": "Lucy",    "dob": "21/04/1984",  "gender": "Female",
        "email": "lucy.phillips.test17@testpatient.com.au", "phone": "0479 901 234",
        "address": "6 Foot Street",      "suburb": "Warrnambool", "state": "VIC", "postcode": "3280",
        "medicare": "2987 65432 7",  "medicare_ref": "1",
        "emergency_name": "Ian Phillips",   "emergency_phone": "0479 111 017",  "emergency_relation": "Father",
        "health_fund": "BUPA",       "health_fund_number": "BUP100017",
    },
    {
        "title": "Ms",   "first_name": "Nora",       "last_name": "Murphy",
        "preferred_name": "Nora",    "dob": "13/11/1990",  "gender": "Female",
        "email": "nora.murphy.test18@testpatient.com.au",   "phone": "0490 012 345",
        "address": "19 Hargreaves Street","suburb": "Mildura",    "state": "VIC", "postcode": "3500",
        "medicare": "3098 76543 8",  "medicare_ref": "1",
        "emergency_name": "Sean Murphy",    "emergency_phone": "0490 111 018",  "emergency_relation": "Father",
        "health_fund": "HCF",        "health_fund_number": "HCF100018",
    },
    {
        "title": "Mr",   "first_name": "Luke",       "last_name": "Stewart",
        "preferred_name": "Luke",    "dob": "04/06/1998",  "gender": "Male",
        "email": "luke.stewart.test19@testpatient.com.au",  "phone": "0411 123 456",
        "address": "42 Lonsdale Street",  "suburb": "Dandenong",  "state": "VIC", "postcode": "3175",
        "medicare": "4109 87654 9",  "medicare_ref": "1",
        "emergency_name": "Pam Stewart",    "emergency_phone": "0411 111 019",  "emergency_relation": "Mother",
        "health_fund": "NIB",        "health_fund_number": "NIB100019",
    },
    {
        "title": "Mr",   "first_name": "Jake",       "last_name": "Rogers",
        "preferred_name": "Jake",    "dob": "31/01/1976",  "gender": "Male",
        "email": "jake.rogers.test20@testpatient.com.au",   "phone": "0422 234 567",
        "address": "8 Albert Street",    "suburb": "Wodonga",     "state": "VIC", "postcode": "3690",
        "medicare": "5210 98765 0",  "medicare_ref": "1",
        "emergency_name": "Tina Rogers",    "emergency_phone": "0422 111 020",  "emergency_relation": "Spouse",
        "health_fund": "AHM",        "health_fund_number": "AHM100020",
    },
    # ── QLD ──────────────────────────────────────────────────────────────────
    {
        "title": "Ms",   "first_name": "Sarah",      "last_name": "Thompson",
        "preferred_name": "Sarah",   "dob": "09/09/1986",  "gender": "Female",
        "email": "sarah.thompson.test21@testpatient.com.au","phone": "0433 345 678",
        "address": "25 Queen Street",    "suburb": "Brisbane",    "state": "QLD", "postcode": "4000",
        "medicare": "6321 09876 1",  "medicare_ref": "1",
        "emergency_name": "Paul Thompson",  "emergency_phone": "0433 111 021",  "emergency_relation": "Father",
        "health_fund": "Medibank",   "health_fund_number": "MBK100021",
    },
    {
        "title": "Ms",   "first_name": "Chloe",      "last_name": "Robinson",
        "preferred_name": "Chloe",   "dob": "17/03/1994",  "gender": "Female",
        "email": "chloe.robinson.test22@testpatient.com.au","phone": "0444 456 789",
        "address": "77 Orchid Avenue",   "suburb": "Surfers Paradise","state": "QLD","postcode": "4217",
        "medicare": "7432 10987 2",  "medicare_ref": "1",
        "emergency_name": "Nick Robinson",  "emergency_phone": "0444 111 022",  "emergency_relation": "Father",
        "health_fund": "BUPA",       "health_fund_number": "BUP100022",
    },
    {
        "title": "Mr",   "first_name": "Nathan",     "last_name": "Allen",
        "preferred_name": "Nate",    "dob": "26/07/1982",  "gender": "Male",
        "email": "nathan.allen.test23@testpatient.com.au",  "phone": "0455 567 890",
        "address": "10 Flinders Street", "suburb": "Townsville",  "state": "QLD", "postcode": "4810",
        "medicare": "8543 21098 3",  "medicare_ref": "1",
        "emergency_name": "Kate Allen",     "emergency_phone": "0455 111 023",  "emergency_relation": "Spouse",
        "health_fund": "HCF",        "health_fund_number": "HCF100023",
    },
    {
        "title": "Mrs",  "first_name": "Hannah",     "last_name": "Mitchell",
        "preferred_name": "Hannah",  "dob": "01/12/1970",  "gender": "Female",
        "email": "hannah.mitchell.test24@testpatient.com.au","phone": "0466 678 901",
        "address": "38 Shield Street",   "suburb": "Cairns",      "state": "QLD", "postcode": "4870",
        "medicare": "9654 32109 4",  "medicare_ref": "1",
        "emergency_name": "Rick Mitchell",  "emergency_phone": "0466 111 024",  "emergency_relation": "Spouse",
        "health_fund": "NIB",        "health_fund_number": "NIB100024",
    },
    {
        "title": "Mr",   "first_name": "Thomas",     "last_name": "Campbell",
        "preferred_name": "Tom",     "dob": "23/05/1999",  "gender": "Male",
        "email": "thomas.campbell.test25@testpatient.com.au","phone": "0477 789 012",
        "address": "52 Ruthven Street",  "suburb": "Toowoomba",   "state": "QLD", "postcode": "4350",
        "medicare": "2765 43210 5",  "medicare_ref": "1",
        "emergency_name": "Mary Campbell",  "emergency_phone": "0477 111 025",  "emergency_relation": "Mother",
        "health_fund": "AHM",        "health_fund_number": "AHM100025",
    },
    {
        "title": "Ms",   "first_name": "Amelia",     "last_name": "Parker",
        "preferred_name": "Amy",     "dob": "10/08/1989",  "gender": "Female",
        "email": "amelia.parker.test26@testpatient.com.au", "phone": "0488 890 123",
        "address": "16 Bayview Street",  "suburb": "Hervey Bay",  "state": "QLD", "postcode": "4655",
        "medicare": "3876 54321 6",  "medicare_ref": "1",
        "emergency_name": "Bruce Parker",   "emergency_phone": "0488 111 026",  "emergency_relation": "Father",
        "health_fund": "Medibank",   "health_fund_number": "MBK100026",
    },
    {
        "title": "Ms",   "first_name": "Aria",       "last_name": "Morris",
        "preferred_name": "Aria",    "dob": "06/02/1995",  "gender": "Female",
        "email": "aria.morris.test27@testpatient.com.au",   "phone": "0499 901 234",
        "address": "29 Nebo Road",       "suburb": "Mackay",      "state": "QLD", "postcode": "4740",
        "medicare": "4987 65432 7",  "medicare_ref": "1",
        "emergency_name": "Gary Morris",    "emergency_phone": "0499 111 027",  "emergency_relation": "Father",
        "health_fund": "BUPA",       "health_fund_number": "BUP100027",
    },
    {
        "title": "Mr",   "first_name": "Dylan",      "last_name": "Cook",
        "preferred_name": "Dyl",     "dob": "15/10/1977",  "gender": "Male",
        "email": "dylan.cook.test28@testpatient.com.au",    "phone": "0410 012 345",
        "address": "4 Bourbong Street",  "suburb": "Bundaberg",   "state": "QLD", "postcode": "4670",
        "medicare": "5098 76543 8",  "medicare_ref": "1",
        "emergency_name": "Val Cook",       "emergency_phone": "0410 111 028",  "emergency_relation": "Spouse",
        "health_fund": "HCF",        "health_fund_number": "HCF100028",
    },
    {
        "title": "Mr",   "first_name": "Liam",       "last_name": "Bailey",
        "preferred_name": "Liam",    "dob": "28/04/2001",  "gender": "Male",
        "email": "liam.bailey.test29@testpatient.com.au",   "phone": "0421 123 456",
        "address": "63 Goondoon Street", "suburb": "Gladstone",   "state": "QLD", "postcode": "4680",
        "medicare": "6109 87654 9",  "medicare_ref": "1",
        "emergency_name": "Jenny Bailey",   "emergency_phone": "0421 111 029",  "emergency_relation": "Mother",
        "health_fund": "NIB",        "health_fund_number": "NIB100029",
    },
    {
        "title": "Ms",   "first_name": "Ellie",      "last_name": "Rivera",
        "preferred_name": "Ellie",   "dob": "12/06/1985",  "gender": "Female",
        "email": "ellie.rivera.test30@testpatient.com.au",  "phone": "0432 234 567",
        "address": "18 East Street",     "suburb": "Rockhampton", "state": "QLD", "postcode": "4700",
        "medicare": "7210 98765 0",  "medicare_ref": "1",
        "emergency_name": "Carlos Rivera",  "emergency_phone": "0432 111 030",  "emergency_relation": "Father",
        "health_fund": "AHM",        "health_fund_number": "AHM100030",
    },
    # ── WA ───────────────────────────────────────────────────────────────────
    {
        "title": "Mr",   "first_name": "Robert",     "last_name": "Taylor",
        "preferred_name": "Rob",     "dob": "20/01/1973",  "gender": "Male",
        "email": "robert.taylor.test31@testpatient.com.au", "phone": "0443 345 678",
        "address": "100 St Georges Terrace","suburb": "Perth",    "state": "WA",  "postcode": "6000",
        "medicare": "8321 09876 1",  "medicare_ref": "1",
        "emergency_name": "Linda Taylor",   "emergency_phone": "0443 111 031",  "emergency_relation": "Spouse",
        "health_fund": "HBF",        "health_fund_number": "HBF100031",
    },
    {
        "title": "Ms",   "first_name": "Grace",      "last_name": "Hall",
        "preferred_name": "Grace",   "dob": "08/09/1991",  "gender": "Female",
        "email": "grace.hall.test32@testpatient.com.au",    "phone": "0454 456 789",
        "address": "31 High Street",     "suburb": "Fremantle",   "state": "WA",  "postcode": "6160",
        "medicare": "9432 10987 2",  "medicare_ref": "1",
        "emergency_name": "Tom Hall",       "emergency_phone": "0454 111 032",  "emergency_relation": "Father",
        "health_fund": "HBF",        "health_fund_number": "HBF100032",
    },
    {
        "title": "Ms",   "first_name": "Ava",        "last_name": "Scott",
        "preferred_name": "Ava",     "dob": "24/03/1997",  "gender": "Female",
        "email": "ava.scott.test33@testpatient.com.au",     "phone": "0465 567 890",
        "address": "7 Victoria Street",  "suburb": "Bunbury",     "state": "WA",  "postcode": "6230",
        "medicare": "2543 21098 3",  "medicare_ref": "1",
        "emergency_name": "Lyn Scott",      "emergency_phone": "0465 111 033",  "emergency_relation": "Mother",
        "health_fund": "Medibank",   "health_fund_number": "MBK100033",
    },
    {
        "title": "Mr",   "first_name": "Alexander",  "last_name": "Adams",
        "preferred_name": "Alex",    "dob": "16/11/1981",  "gender": "Male",
        "email": "alexander.adams.test34@testpatient.com.au","phone": "0476 678 901",
        "address": "44 Marine Terrace",  "suburb": "Geraldton",   "state": "WA",  "postcode": "6530",
        "medicare": "3654 32109 4",  "medicare_ref": "1",
        "emergency_name": "Rachel Adams",   "emergency_phone": "0476 111 034",  "emergency_relation": "Spouse",
        "health_fund": "BUPA",       "health_fund_number": "BUP100034",
    },
    {
        "title": "Ms",   "first_name": "Zoe",        "last_name": "Roberts",
        "preferred_name": "Zoe",     "dob": "03/07/1988",  "gender": "Female",
        "email": "zoe.roberts.test35@testpatient.com.au",   "phone": "0487 789 012",
        "address": "19 Stirling Street", "suburb": "Northam",     "state": "WA",  "postcode": "6401",
        "medicare": "4765 43210 5",  "medicare_ref": "1",
        "emergency_name": "Neil Roberts",   "emergency_phone": "0487 111 035",  "emergency_relation": "Father",
        "health_fund": "HCF",        "health_fund_number": "HCF100035",
    },
    {
        "title": "Mr",   "first_name": "Ryan",       "last_name": "Evans",
        "preferred_name": "Ryan",    "dob": "11/04/1966",  "gender": "Male",
        "email": "ryan.evans.test36@testpatient.com.au",    "phone": "0498 890 123",
        "address": "6 Wittenoom Street", "suburb": "Albany",      "state": "WA",  "postcode": "6330",
        "medicare": "5876 54321 6",  "medicare_ref": "1",
        "emergency_name": "Carol Evans",    "emergency_phone": "0498 111 036",  "emergency_relation": "Spouse",
        "health_fund": "NIB",        "health_fund_number": "NIB100036",
    },
    {
        "title": "Ms",   "first_name": "Hazel",      "last_name": "Morgan",
        "preferred_name": "Hazel",   "dob": "29/08/2002",  "gender": "Female",
        "email": "hazel.morgan.test37@testpatient.com.au",  "phone": "0409 901 234",
        "address": "55 Chamberlain Street","suburb": "Kalgoorlie","state": "WA",  "postcode": "6430",
        "medicare": "6987 65432 7",  "medicare_ref": "1",
        "emergency_name": "Pat Morgan",     "emergency_phone": "0409 111 037",  "emergency_relation": "Mother",
        "health_fund": "HBF",        "health_fund_number": "HBF100037",
    },
    {
        "title": "Mr",   "first_name": "Joshua",     "last_name": "Walker",
        "preferred_name": "Josh",    "dob": "07/02/1979",  "gender": "Male",
        "email": "joshua.walker.test38@testpatient.com.au", "phone": "0420 012 345",
        "address": "12 Durlacher Street","suburb": "Geraldton",   "state": "WA",  "postcode": "6530",
        "medicare": "7098 76543 8",  "medicare_ref": "1",
        "emergency_name": "Sue Walker",     "emergency_phone": "0420 111 038",  "emergency_relation": "Spouse",
        "health_fund": "AHM",        "health_fund_number": "AHM100038",
    },
    # ── SA ───────────────────────────────────────────────────────────────────
    {
        "title": "Ms",   "first_name": "Jessica",    "last_name": "Brown",
        "preferred_name": "Jess",    "dob": "15/06/1990",  "gender": "Female",
        "email": "jessica.brown.test39@testpatient.com.au", "phone": "0431 123 456",
        "address": "72 King William Street","suburb": "Adelaide",  "state": "SA",  "postcode": "5000",
        "medicare": "8109 87654 9",  "medicare_ref": "1",
        "emergency_name": "Dan Brown",      "emergency_phone": "0431 111 039",  "emergency_relation": "Father",
        "health_fund": "Medibank",   "health_fund_number": "MBK100039",
    },
    {
        "title": "Mr",   "first_name": "Benjamin",   "last_name": "King",
        "preferred_name": "Ben",     "dob": "23/10/1983",  "gender": "Male",
        "email": "benjamin.king.test40@testpatient.com.au", "phone": "0442 234 567",
        "address": "9 Moseley Street",   "suburb": "Glenelg",     "state": "SA",  "postcode": "5045",
        "medicare": "9210 98765 0",  "medicare_ref": "1",
        "emergency_name": "Angela King",    "emergency_phone": "0442 111 040",  "emergency_relation": "Spouse",
        "health_fund": "BUPA",       "health_fund_number": "BUP100040",
    },
    {
        "title": "Mr",   "first_name": "Jack",       "last_name": "Perez",
        "preferred_name": "Jack",    "dob": "01/05/1974",  "gender": "Male",
        "email": "jack.perez.test41@testpatient.com.au",    "phone": "0453 345 678",
        "address": "34 Commercial Road", "suburb": "Port Adelaide","state": "SA",  "postcode": "5015",
        "medicare": "2321 09876 1",  "medicare_ref": "1",
        "emergency_name": "Maria Perez",    "emergency_phone": "0453 111 041",  "emergency_relation": "Spouse",
        "health_fund": "HCF",        "health_fund_number": "HCF100041",
    },
    {
        "title": "Ms",   "first_name": "Violet",     "last_name": "Reed",
        "preferred_name": "Vi",      "dob": "18/12/1998",  "gender": "Female",
        "email": "violet.reed.test42@testpatient.com.au",   "phone": "0464 456 789",
        "address": "22 Commercial Street","suburb": "Mount Gambier","state": "SA", "postcode": "5290",
        "medicare": "3432 10987 2",  "medicare_ref": "1",
        "emergency_name": "Owen Reed",      "emergency_phone": "0464 111 042",  "emergency_relation": "Father",
        "health_fund": "NIB",        "health_fund_number": "NIB100042",
    },
    {
        "title": "Ms",   "first_name": "Scarlett",   "last_name": "Morris",
        "preferred_name": "Scar",    "dob": "09/07/1986",  "gender": "Female",
        "email": "scarlett.morris.test43@testpatient.com.au","phone": "0475 567 890",
        "address": "5 Wright Road",      "suburb": "Whyalla",     "state": "SA",  "postcode": "5600",
        "medicare": "4543 21098 3",  "medicare_ref": "1",
        "emergency_name": "Kevin Morris",   "emergency_phone": "0475 111 043",  "emergency_relation": "Spouse",
        "health_fund": "AHM",        "health_fund_number": "AHM100043",
    },
    # ── TAS ──────────────────────────────────────────────────────────────────
    {
        "title": "Mrs",  "first_name": "Isabella",   "last_name": "White",
        "preferred_name": "Bella",   "dob": "27/03/1993",  "gender": "Female",
        "email": "isabella.white.test44@testpatient.com.au","phone": "0486 678 901",
        "address": "66 Liverpool Street","suburb": "Hobart",      "state": "TAS", "postcode": "7000",
        "medicare": "5654 32109 4",  "medicare_ref": "1",
        "emergency_name": "Chris White",    "emergency_phone": "0486 111 044",  "emergency_relation": "Spouse",
        "health_fund": "Medibank",   "health_fund_number": "MBK100044",
    },
    {
        "title": "Mr",   "first_name": "Lachlan",    "last_name": "Hughes",
        "preferred_name": "Lach",    "dob": "14/09/1971",  "gender": "Male",
        "email": "lachlan.hughes.test45@testpatient.com.au","phone": "0497 789 012",
        "address": "31 St John Street",  "suburb": "Launceston",  "state": "TAS", "postcode": "7250",
        "medicare": "6765 43210 5",  "medicare_ref": "1",
        "emergency_name": "Wendy Hughes",   "emergency_phone": "0497 111 045",  "emergency_relation": "Spouse",
        "health_fund": "BUPA",       "health_fund_number": "BUP100045",
    },
    {
        "title": "Ms",   "first_name": "Zara",       "last_name": "Price",
        "preferred_name": "Zara",    "dob": "06/01/2003",  "gender": "Female",
        "email": "zara.price.test46@testpatient.com.au",    "phone": "0408 890 123",
        "address": "8 Forbes Street",    "suburb": "Devonport",   "state": "TAS", "postcode": "7310",
        "medicare": "7876 54321 6",  "medicare_ref": "1",
        "emergency_name": "Fran Price",     "emergency_phone": "0408 111 046",  "emergency_relation": "Mother",
        "health_fund": "HCF",        "health_fund_number": "HCF100046",
    },
    # ── ACT ──────────────────────────────────────────────────────────────────
    {
        "title": "Mr",   "first_name": "Daniel",     "last_name": "Harris",
        "preferred_name": "Dan",     "dob": "20/08/1987",  "gender": "Male",
        "email": "daniel.harris.test47@testpatient.com.au", "phone": "0419 901 234",
        "address": "17 Garema Place",    "suburb": "Canberra",    "state": "ACT", "postcode": "2601",
        "medicare": "8987 65432 7",  "medicare_ref": "1",
        "emergency_name": "Kim Harris",     "emergency_phone": "0419 111 047",  "emergency_relation": "Spouse",
        "health_fund": "NIB",        "health_fund_number": "NIB100047",
    },
    {
        "title": "Ms",   "first_name": "Freya",      "last_name": "Bennett",
        "preferred_name": "Freya",   "dob": "11/04/1994",  "gender": "Female",
        "email": "freya.bennett.test48@testpatient.com.au", "phone": "0430 012 345",
        "address": "3 Woolley Street",   "suburb": "Dickson",     "state": "ACT", "postcode": "2602",
        "medicare": "9098 76543 8",  "medicare_ref": "1",
        "emergency_name": "Alan Bennett",   "emergency_phone": "0430 111 048",  "emergency_relation": "Father",
        "health_fund": "AHM",        "health_fund_number": "AHM100048",
    },
    # ── NT ───────────────────────────────────────────────────────────────────
    {
        "title": "Mr",   "first_name": "Marcus",     "last_name": "Sullivan",
        "preferred_name": "Marc",    "dob": "25/11/1980",  "gender": "Male",
        "email": "marcus.sullivan.test49@testpatient.com.au","phone": "0441 123 456",
        "address": "48 Smith Street",    "suburb": "Darwin",      "state": "NT",  "postcode": "0800",
        "medicare": "2109 87651 9",  "medicare_ref": "1",
        "emergency_name": "Gail Sullivan",  "emergency_phone": "0441 111 049",  "emergency_relation": "Spouse",
        "health_fund": "Medibank",   "health_fund_number": "MBK100049",
    },
    {
        "title": "Mrs",  "first_name": "Penelope",   "last_name": "Walsh",
        "preferred_name": "Penny",   "dob": "17/06/1976",  "gender": "Female",
        "email": "penelope.walsh.test50@testpatient.com.au","phone": "0452 234 567",
        "address": "12 Todd Street",     "suburb": "Alice Springs","state": "NT",  "postcode": "0870",
        "medicare": "3210 98762 0",  "medicare_ref": "1",
        "emergency_name": "Steve Walsh",    "emergency_phone": "0452 111 050",  "emergency_relation": "Spouse",
        "health_fund": "BUPA",       "health_fund_number": "BUP100050",
    },
]

# ── Generic helpers ───────────────────────────────────────────────────────────

async def try_fill(page, label: str, value: str, timeout: int = 4_000) -> bool:
    """Fill a field by label, placeholder, name, or id — first match wins."""
    slug  = label.lower().replace(" ", "")
    slugu = label.lower().replace(" ", "_")
    candidates = [
        lambda: page.get_by_label(label, exact=False),
        lambda: page.get_by_placeholder(label, exact=False),
        page.locator(f'input[name*="{slug}"]'),
        page.locator(f'input[name*="{slugu}"]'),
        page.locator(f'input[id*="{slug}"]'),
        page.locator(f'input[id*="{slugu}"]'),
        page.locator(f'textarea[name*="{slug}"]'),
    ]
    for c in candidates:
        try:
            loc = c() if callable(c) else c
            await loc.first.wait_for(state="visible", timeout=timeout)
            await loc.first.clear()
            await loc.first.fill(value)
            return True
        except Exception:
            continue
    return False


async def try_select(page, label: str, value: str, timeout: int = 4_000) -> bool:
    """Select a dropdown option by label text or option value."""
    slug  = label.lower().replace(" ", "")
    slugu = label.lower().replace(" ", "_")
    candidates = [
        lambda: page.get_by_label(label, exact=False),
        page.locator(f'select[name*="{slug}"]'),
        page.locator(f'select[name*="{slugu}"]'),
        page.locator(f'select[id*="{slug}"]'),
    ]
    for c in candidates:
        try:
            loc = c() if callable(c) else c
            await loc.first.wait_for(state="visible", timeout=timeout)
            try:
                await loc.first.select_option(label=value)
            except Exception:
                await loc.first.select_option(value=value)
            return True
        except Exception:
            continue
    # Fallback: custom dropdown — click the trigger then pick the option
    try:
        trigger = page.get_by_label(label, exact=False).first
        await trigger.wait_for(state="visible", timeout=timeout)
        await trigger.click()
        option = page.get_by_role("option", name=value, exact=False)
        await option.wait_for(state="visible", timeout=3_000)
        await option.click()
        return True
    except Exception:
        pass
    # Last resort: visible text click (radio groups)
    try:
        opt = page.get_by_text(value, exact=True).first
        await opt.wait_for(state="visible", timeout=timeout)
        await opt.click()
        return True
    except Exception:
        pass
    return False


async def click_button(page, *names: str, timeout: int = 4_000) -> str | None:
    for name in names:
        for role in ("button", "link"):
            try:
                btn = page.get_by_role(role, name=name, exact=False)
                await btn.first.wait_for(state="visible", timeout=timeout)
                await btn.first.scroll_into_view_if_needed()
                await btn.first.click()
                return name
            except PWTimeout:
                continue
    return None


# ── OzMed-specific registration flow ─────────────────────────────────────────

async def register_patient(page, p: dict, idx: int) -> dict:
    total  = len(PATIENTS)
    tag    = f"[{idx:02d}/{total}]"
    result = {
        "index": idx,
        "name":  f"{p['first_name']} {p['last_name']}",
        "email": p["email"],
        "state": p["state"],
        "status": "FAIL",
        "detail": "",
    }

    try:
        print(f"\n{tag} {p['first_name']} {p['last_name']} ({p['state']}) ...")

        await page.goto(URL, wait_until="networkidle", timeout=30_000)
        await page.wait_for_function(
            "() => { const r = document.getElementById('root'); return r && r.children.length > 0; }",
            timeout=15_000,
        )

        # ── Step 1: Click "Create an account" ────────────────────────────────
        clicked = await click_button(page,
            "Create an account", "Create Account", "Register", "Sign up",
            "New patient", "New Patient", "Create patient",
            timeout=8_000,
        )
        if not clicked:
            result["detail"] = "Create an account button not found"
            return result

        await page.wait_for_load_state("networkidle", timeout=10_000)
        await asyncio.sleep(1)

        # ── Step 2: Personal details ──────────────────────────────────────────
        await try_select(page, "Title",          p["title"])
        await try_select(page, "Salutation",     p["title"])
        await try_fill(page,   "First name",     p["first_name"])
        await try_fill(page,   "Given name",     p["first_name"])
        await try_fill(page,   "Last name",      p["last_name"])
        await try_fill(page,   "Surname",        p["last_name"])
        await try_fill(page,   "Family name",    p["last_name"])
        await try_fill(page,   "Preferred name", p["preferred_name"])
        await try_fill(page,   "Preferred",      p["preferred_name"])
        await try_fill(page,   "Date of birth",  p["dob"])
        await try_fill(page,   "Date of Birth",  p["dob"])
        await try_fill(page,   "DOB",            p["dob"])
        await try_fill(page,   "Birthday",       p["dob"])
        await try_select(page, "Gender",         p["gender"])
        await try_select(page, "Sex",            p["gender"])

        # ── Step 3: Contact details ───────────────────────────────────────────
        await try_fill(page, "Email",           p["email"])
        await try_fill(page, "Email address",   p["email"])
        await try_fill(page, "Password",        PASSWORD)
        await try_fill(page, "Confirm password",PASSWORD)
        await try_fill(page, "Confirm",         PASSWORD)
        await try_fill(page, "Mobile",          p["phone"])
        await try_fill(page, "Mobile number",   p["phone"])
        await try_fill(page, "Phone",           p["phone"])
        await try_fill(page, "Phone number",    p["phone"])

        # ── Step 4: Address ───────────────────────────────────────────────────
        await try_fill(page, "Address",         p["address"])
        await try_fill(page, "Street address",  p["address"])
        await try_fill(page, "Street",          p["address"])
        await try_fill(page, "Address line 1",  p["address"])
        await try_fill(page, "Suburb",          p["suburb"])
        await try_fill(page, "City",            p["suburb"])
        await try_fill(page, "Town",            p["suburb"])
        await try_select(page, "State",         p["state"])
        await try_select(page, "State/Territory",p["state"])
        await try_fill(page, "Postcode",        p["postcode"])
        await try_fill(page, "Post code",       p["postcode"])
        await try_fill(page, "Zip",             p["postcode"])

        # ── Step 5: Medicare ──────────────────────────────────────────────────
        await try_fill(page, "Medicare",           p["medicare"])
        await try_fill(page, "Medicare number",    p["medicare"])
        await try_fill(page, "Medicare card",      p["medicare"])
        await try_fill(page, "Medicare card number",p["medicare"])
        await try_fill(page, "Medicare reference", p["medicare_ref"])
        await try_fill(page, "Reference number",   p["medicare_ref"])
        await try_fill(page, "IRN",                p["medicare_ref"])

        # ── Step 6: Emergency contact ─────────────────────────────────────────
        await try_fill(page, "Emergency contact",       p["emergency_name"])
        await try_fill(page, "Emergency contact name",  p["emergency_name"])
        await try_fill(page, "Next of kin",             p["emergency_name"])
        await try_fill(page, "Emergency phone",         p["emergency_phone"])
        await try_fill(page, "Emergency contact phone", p["emergency_phone"])
        await try_fill(page, "Next of kin phone",       p["emergency_phone"])
        await try_fill(page, "Relationship",            p["emergency_relation"])
        await try_select(page,"Relationship",           p["emergency_relation"])

        # ── Step 7: Health fund ───────────────────────────────────────────────
        await try_fill(page,   "Health fund",        p["health_fund"])
        await try_select(page, "Health fund",        p["health_fund"])
        await try_fill(page,   "Private health",     p["health_fund"])
        await try_select(page, "Private health",     p["health_fund"])
        await try_fill(page,   "Health fund number", p["health_fund_number"])
        await try_fill(page,   "Member number",      p["health_fund_number"])
        await try_fill(page,   "Membership number",  p["health_fund_number"])

        # ── Step 8: Multi-step — click Next/Continue if form is paginated ─────
        for _ in range(5):
            advanced = await click_button(page, "Next", "Continue", timeout=2_000)
            if not advanced:
                break
            await asyncio.sleep(0.8)

        # ── Step 9: Final submit ──────────────────────────────────────────────
        submitted = await click_button(page,
            "Register", "Create account", "Create patient", "Create Patient",
            "Sign up", "Submit", "Save", "Confirm",
            timeout=5_000,
        )
        if not submitted:
            shot = os.path.join(SCREENSHOT_DIR, f"patient_{idx:02d}_no_submit.png")
            await page.screenshot(path=shot, full_page=True)
            result["detail"] = f"Submit button not found — see {shot}"
            return result

        # Wait for result
        try:
            await page.wait_for_url(lambda u: u != URL, timeout=7_000)
        except PWTimeout:
            pass
        await asyncio.sleep(2)

        shot = os.path.join(SCREENSHOT_DIR, f"patient_{idx:02d}_result.png")
        await page.screenshot(path=shot, full_page=True)

        body = (await page.inner_text("body")).lower()
        errors = ["error", "invalid", "already exists", "already registered", "failed", "required"]
        if any(e in body for e in errors):
            result["status"] = "WARN"
            result["detail"] = f"Possible error after submit — URL: {page.url}"
        else:
            result["status"] = "OK"
            result["detail"] = f"OK — {page.url}"

        print(f"      {result['status']} → {result['detail'][:80]}")

    except Exception as exc:
        result["detail"] = str(exc)[:300]
        print(f"      FAIL: {result['detail']}")
        try:
            shot = os.path.join(SCREENSHOT_DIR, f"patient_{idx:02d}_error.png")
            await page.screenshot(path=shot, full_page=True)
        except Exception:
            pass

    return result


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    results = []
    start   = datetime.now()

    print(f"\n{'='*65}")
    print(f"  OzMed — Registering {len(PATIENTS)} Australian patients")
    print(f"  Target : {URL}")
    print(f"  Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page    = await context.new_page()

        for idx, patient in enumerate(PATIENTS, start=1):
            r = await register_patient(page, patient, idx)
            results.append(r)
            await asyncio.sleep(1.5)

        await browser.close()

    # ── Summary CSV ───────────────────────────────────────────────────────────
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "name", "email", "state", "status", "detail"])
        writer.writeheader()
        writer.writerows(results)

    ok   = sum(1 for r in results if r["status"] == "OK")
    warn = sum(1 for r in results if r["status"] == "WARN")
    fail = sum(1 for r in results if r["status"] == "FAIL")
    secs = int((datetime.now() - start).total_seconds())

    print(f"\n{'='*65}")
    print(f"  Completed in {secs}s")
    print(f"  OK: {ok}   WARN: {warn}   FAIL: {fail}   Total: {len(results)}")
    print(f"  CSV        → {RESULTS_CSV}")
    print(f"  Screenshots→ {SCREENSHOT_DIR}/")
    print(f"{'='*65}\n")

    if fail or warn:
        print("  Patients with issues:")
        for r in results:
            if r["status"] != "OK":
                print(f"    [{r['index']:02d}] {r['name']:25s} {r['status']} — {r['detail'][:60]}")


if __name__ == "__main__":
    asyncio.run(main())
