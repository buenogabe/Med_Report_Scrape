from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.colors import PCMYKColor
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Rect
from reportlab.lib.units import inch
import os, errno
import textwrap
import reportlab.platypus
import sys
from Tkinter import *
from datetime import date

# make reports, records, and statistics directories if not present already
firstTime = False
try:
    os.makedirs('reports')
except OSError as e:
    if e.errno != errno.EEXIST:
        raise
try:
    os.makedirs('records')
    firstTime = True
except OSError as e:
    if e.errno != errno.EEXIST:
        raise
try:
    os.makedirs('statistics')
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

# path
#   these variables store useful paths
recordsPath = os.getcwd() + "/XMLrecords/"
reportsPath = os.getcwd() + "/reports/"
statsPath = os.getcwd() + "/statistics/"

# counts number of XML files in the records directory
numRecords = 0
for f in os.listdir(recordsPath):
    if f.endswith('.XML'):
        numRecords += 1
if numRecords == 0:
    firstTime = True

# initialize sets
#   sets used as a searching database
searchSet = [set() for i in range(0, numRecords)]
medSet = [set() for i in range(0, numRecords)]
diseaseSet = [set() for i in range(0, numRecords)]
recordNames = [None] * numRecords
ageGroup = [None] * numRecords
raceGroup = [None] * numRecords

# race stats
#   initialize an array that counts pop of each race. Lables for x axis of bar graph
raceDist = [0] * 7
raceXAxis = ['', 'White', 'Asian', 'Black', 'Native', 'Other', '']

# age stats
#   initialize array that counts age groups. Lables for histogram
ageDist = [0] * 7
ageXAxis = ['', '0-18', '19-44', '45-64', '65-84', '85+', '']

# disease stats
popDiseaseList = []

# scrape medical records, store info, make pdf for each record
recordCount = 0
for f in os.listdir(recordsPath):
    if f.endswith('.XML'):
        print(f)
        print(recordCount)
        summaryFile = open(os.path.join(recordsPath, f), "r")
        contents = summaryFile.read()
        soup = BeautifulSoup(contents, 'lxml')

        # isFHIR
        if soup.find("realmcode") is None:
            isFHIR = True
        else:
            isFHIR = False

        # Organization
        org = "n/a"
        if not isFHIR:
            org = soup.find("representedorganization")
            org = org.contents[1]
            org = org.text

        # name
        if isFHIR:
            given = soup.find('given').contents[0].text
        else:
            given = soup.find('given').text
        family = soup.find('family').text

        # address
        if isFHIR:
            street = soup.find('line').contents[0]
        else:
            street = soup.find('streetaddressline')
        city = soup.find('city')
        state = soup.find('state')
        zipcode = soup.find('postalcode')
        country = soup.find('country')
        addr = street.text + " " + city.text + ", " + state.text + " " + zipcode.text + " " + country.text

        # phone
        if isFHIR:
            phone = soup.find('telecom')
            phone = phone.contents[0].contents[2].text
        else:
            phone = soup.find("telecom", {"use":"MC"})["value"]
            phone = phone[4:]

        # race
        if isFHIR:
            race = soup.find("valuecoding").contents[2].text
        else:
            if soup.find("racecode").has_attr("displayname"):
                race = soup.find("racecode")["displayname"]
            elif soup.find("racecode").has_attr("nullflavor"):
                race = soup.find("racecode")["nullflavor"]
            else:
                race = ""
        # Record how many of each race there is
        if race == "White":
            raceDist[1] += 1
            raceGroup[recordCount] = 1
        elif race == "Asian":
            raceDist[2] += 1
            raceGroup[recordCount] = 2
        elif race == "Black or African American":
            raceDist[3] += 1
            raceGroup[recordCount] = 3
        elif race == "American Indian or Alaska Native":
            raceDist[4] += 1
            raceGroup[recordCount] = 4
        elif race == "Other" or race == "UNK":
            raceDist[5] += 1
            raceGroup[recordCount] = 5
        # 1: White, 2: Asian, 3: Black, 4: Native, 5: Other

        # dead or alive
        isAlive = True

        if isFHIR:
            if soup.find("deceaseddatetime") != None:
                isAlive = False

                dDate = soup.find("deceaseddatetime").text[:10]
                dYear = int(dDate[:4])
                dMonth = int(dDate[5:7])
                dDay = int(dDate[8:10])
            else:
                dDate = "n/a"
                dYear = "n/a"
                dMonth = "n/a"
                dDay = "n/a"

        else:
            dDate = "n/a"
            dYear = "n/a"
            dMonth = "n/a"
            dDay = "n/a"

        # Cause of Death
        if isFHIR:
            if not isAlive:
                dCause = soup.find_all("valuecodeableconcept")
                dCause = dCause[len(dCause)-1].contents[0].text
                # if patient is dead cause of death is the first child of the last valuecodeableconcept
            else:
                dCause = "n/a"
        else:
            dCause = "n/a"

        # age and birthdate
        if isFHIR:
            bDate = soup.find("birthdate").text
            bYear = int(bDate[:4])
            bMonth = int(bDate[5:7])
            bDay = int(bDate[8:10])

            today = date.today()
            if isAlive:
                age = today.year - bYear - ((today.month, today.day) < (bMonth, bDay))
            else:
                age = dYear - bYear - ((dMonth, dDay) < (bMonth, bDay))
        else:
            bDate = soup.find("birthtime")["value"]
            bYear = int(bDate[:4])
            bMonth = int(bDate[4:6])
            bDay = int(bDate[6:])
            bDate = str(bYear) + "-" + str(bMonth) + "-" + str(bDay)

            # Calculate age based on current date
            today = date.today()
            if isAlive or not isFHIR:
                age = today.year - bYear - ((today.month, today.day) < (bMonth, bDay))
            else:
                age = dYear - bYear - ((dMonth, dDay) < (bMonth, bDay))
        # record how many people are in each age group
        if age <= 18:
            ageDist[1] += 1
            ageGroup[recordCount] = 1
        elif age > 18 and age < 45:
            ageDist[2] += 1
            ageGroup[recordCount] = 2
        elif age > 44 and age < 65:
            ageDist[3] += 1
            ageGroup[recordCount] = 3
        elif age > 64 and age < 85:
            ageDist[4] += 1
            ageGroup[recordCount] = 4
        elif age > 84:
            ageDist[5] += 1
            ageGroup[recordCount] = 5

        # agePercent = [0] * 5
        # i = 0
        # for a in ageDist:
        #     agePercent[i] = round(float(ageDist[i])/float(numRecords), 4) * 100
        #     i+=1
        # 0: 0-18, 1: 19-44, 2: 45-64, 3: 65-84, 4: 85+

        # hospital
        def is_hospital(tag):
            next = tag.next_sibling
            if next is not None:
                if next.name == "resourcetype":
                    next2 = tag.next_sibling.next_sibling
                    if next2 is not None:
                        if next2.name == "contact":
                            return True
                return False

        if isFHIR:
            hospitalName = soup.find(is_hospital).text
        else:
            hospitalName = "n/a"

        # allergies
        if not isFHIR:
            def is_allergy(tag):
                if tag.has_attr("id"):
                    return "allergen" in tag.get("id")
            allergyList = soup.find_all(is_allergy)

            allergyStrings = ["" for x in range(len(allergyList))]
            i = 0
            for a in allergyList:
                allergyStrings[i] = a.get_text()
                i = i + 1

        # medication and dosage
        if isFHIR:
            medicationInfo = soup.find_all("medicationcodeableconcept")
            medicationStrings = ["" for x in range(len(medicationInfo))]
            i = 0
            for m in medicationInfo:
                medicationStrings[i] = medicationInfo[i].contents[1].contents[0].contents[2].text
                i += 1
        else:
            def is_medication(tag):
                if tag.has_attr("id"):
                    return "med" in tag.get("id")
            medicationList = soup.find_all(is_medication)

            medicationStrings = ["" for x in range(len(medicationList))]
            i = 0
            for medication in medicationList:
                medicationStrings[i] = medication.get_text()
                i = i + 1

        # med directions
        if not isFHIR:
            def is_direc(tag):
                if tag.has_attr("id"):

                    return "sig" in tag.get("id")
            direcList = soup.find_all(is_direc)

            direcStrings = ["" for x in range(len(direcList))]
            i = 0
            for direc in direcList:
                direcStrings[i] = direc.get_text()
                direcStrings[i] = '. '.join(i.capitalize() for i in direcStrings[i].split('. '))
                i = i + 1

        # med start date
        if isFHIR:
            medStart = soup.find_all("authoredon")
            medStartStrings = ["" for x in range(len(medStart))]
            i = 0
            for s in medStart:
                medStartStrings[i] = medStart[i].text
                medStartStrings[i] = medStartStrings[i][:10]
                i += 1
        else:
            def is_start(tag):
                if "Sutter" in org:
                    prev = tag.previous_sibling
                    if prev is None:
                        return False
                    if not hasattr(prev, "has_attr"):
                        return False
                    if prev.has_attr("id"):
                        return "med" in prev.get("id")
                else:
                    prev = tag.previous_sibling
                    if prev is None:
                        return False
                    prev = prev.previous_sibling
                    if prev is None:
                        return False
                    if not hasattr(prev, "has_attr"):
                        return False
                    if prev.has_attr("id"):
                        if "sig" in prev.get("id"):
                            return "sig" in prev.get("id")
                        elif "med" in prev.get("id"):
                            return "med" in prev.get("id")
                    return False
            startList = soup.find_all(is_start)

            medStartStrings = ["" for x in range(len(medicationList))]
            i = 0
            for start in startList:
                medStartStrings[i] = start.get_text()
                i = i + 1

        # med end date
        if not isFHIR:
            def is_end(tag):
                prev = tag.previous_sibling
                if prev is None:
                    return False
                prev = prev.previous_sibling
                if prev is None:
                    return False
                prev = prev.previous_sibling
                if prev is None:
                    return False
                if not hasattr(prev, "has_attr"):
                    return False
                if prev.has_attr("id"):
                    return "sig" in prev.get("id")
                return False
            endList = soup.find_all(is_end)

            endStrings = ["" for x in range(len(medicationList))]
            i = 0
            for end in endList:
                endStrings[i] = end.get_text()
                i = i + 1

        # med active status
        if isFHIR:
            active = soup.find_all("medicationcodeableconcept")
            i = 0
            activeStrings = ["" for x in range(len(active))]
            for a in active:
                #for r in range(7):
                while active[i].name != "status":
                    active[i] = active[i].previous_sibling
                activeStrings[i] = active[i].text.capitalize()
                i += 1
        else:
            def is_active(tag):
                prev = tag.previous_sibling
                if prev is None:
                    return False
                prev = prev.previous_sibling
                if prev is None:
                    return False
                prev = prev.previous_sibling
                if prev is None:
                    return False
                prev = prev.previous_sibling
                if prev is None:
                    return False
                if not hasattr(prev, "has_attr"):
                    return False
                return is_direc(prev)
            activeList = soup.find_all(is_active)

            activeStrings = ["" for x in range(len(medicationList))]
            i = 0
            for active in activeList:
                activeStrings[i] = active.get_text()
                i = i + 1

        # shots
        if isFHIR:
            shotInfo = soup.find_all("vaccinecode")
            shotStrings = ["" for x in range(len(shotInfo))]
            j = 0
            for i in shotInfo:
                shotStrings[j] = shotInfo[j].contents[0].text  # .contents[1].contents[3]
                j += 1
            shotdateInfo = soup.find_all("vaccinecode")
            shotdateStrings = ["" for x in range(len(shotdateInfo))]
            i = 0
            for a in shotdateInfo:
                shotdateStrings[i] = shotdateInfo[i].next_sibling.next_sibling.next_sibling.text
                i += 1
        else:
            def is_shot(tag):
                if tag.has_attr("id"):
                    return "immunization" in tag.get("id")
            shotList = soup.find_all(is_shot)

            shotStrings = ["" for x in range(len(shotList))]
            i = 0
            for s in shotList:
                shotStrings[i] = s.get_text()
                i = i + 1
            # Active Problems
            def is_problem(tag):
                if tag.has_attr("id"):
                    return "problem" in tag.get("id")
            probList = soup.find_all(is_problem)

            probStrings = ["" for x in range(len(probList))]
            i = 0
            for p in probList:
                probStrings[i] = p.get_text()
                i = i + 1

        # diseases
        if isFHIR:
            diseaseInfo = soup.find_all("asserteddate")
            diseaseStrings = ["" for x in range(len(diseaseInfo))]
            diseasedateStrings = ["" for x in range(len(diseaseInfo))]
            j = 0
            for i in diseaseInfo:
                diseaseStrings[j] = diseaseInfo[j].next_sibling.contents[0].text
                diseasedateStrings[j] = diseaseInfo[j].text[:10]
                j += 1
        else:
            diseaseStrings = ""
            diseasedateStrings = ""

        # Placeholder values
        if isFHIR:
            allergyStrings = "" # ["" for x in range(len(medicationStrings))]
            direcStrings = ["" for x in range(len(medicationStrings))]
            # medStartStrings = ["" for x in range(len(medicationStrings))]
            endStrings = ["" for x in range(len(medicationStrings))]
            # activeStrings = ["" for x in range(len(medicationStrings))]
            probStrings = "" # ["" for x in range(len(medicationStrings))]

        # Add values to searchSet
        searchSet[recordCount].add(given.lower())
        searchSet[recordCount].add(family.lower())
        searchSet[recordCount].add(addr.lower())
        searchSet[recordCount].add(phone.lower())
        searchSet[recordCount].add(race.lower())
        searchSet[recordCount].add(bDate.lower())
        searchSet[recordCount].add(dDate.lower())
        searchSet[recordCount].add(hospitalName.lower())
        searchSet[recordCount].add(dCause.lower())

        i = 0
        for a in allergyStrings:
            searchSet[recordCount].add(allergyStrings[i].lower())
            i += 1
        i = 0
        for m in medicationStrings:
            searchSet[recordCount].add(medicationStrings[i].lower())
            medSet[recordCount].add(medicationStrings[i].lower())
            i += 1
        i = 0
        for d in direcStrings:
            searchSet[recordCount].add(direcStrings[i].lower())
            i += 1
        i = 0
        for m in medStartStrings:
            searchSet[recordCount].add(medStartStrings[i].lower())
            i += 1
        i = 0
        for e in endStrings:
            searchSet[recordCount].add(endStrings[i].lower())
            i += 1
        i = 0
        for a in activeStrings:
            searchSet[recordCount].add(activeStrings[i].lower())
            i += 1
        i = 0
        for s in shotStrings:
            searchSet[recordCount].add(shotStrings[i].lower())
            i += 1
        i = 0
        for p in probStrings:
            searchSet[recordCount].add(probStrings[i].lower())
            i += 1
        i = 0
        for d in diseaseStrings:
            searchSet[recordCount].add(diseaseStrings[i].lower())
            searchSet[recordCount].add(diseasedateStrings[i].lower())
            diseaseSet[recordCount].add(diseaseStrings[i].lower())
            popDiseaseList.append(diseaseStrings[i].lower())
            i += 1
        # make PDF
        c = canvas.Canvas(reportsPath + given + "_report" +  ".pdf")
        recordNames[recordCount] = given + "_report" +  ".pdf"
        # c.setFillColorRGB(255,0,98)

        # Title
        c.setFont("Helvetica-Bold", 14)
        c.drawString(225, 820, "Patient Health Summary")

        # Page Number
        pageNum = 1
        c.setFont("Helvetica", 12)
        c.drawString(540, 20, "Page 1")

        xLeft = 30
        xIndent = xLeft + 20
        yStart = 790
        gap = 15
        g = 3

        # Patient Info: Name, addr, race, phone
        c.setFont("Helvetica-Bold", 12)
        c.drawString(xLeft, yStart, "Patient Info")
        c.setFont("Helvetica", 7)
        c.drawString(xIndent, yStart - gap, "Name: " + given + " " + family)
        addrString = "Address: " + addr
        aSpace = 0
        if len(addrString) > 70:
            wrap_text = textwrap.wrap(addrString, width = 70)
            c.drawString(xIndent, yStart - gap * 2, wrap_text[0])
            c.drawString(xIndent + 30, yStart - gap - 23, wrap_text[1])
            c.drawString(xIndent, yStart - gap * 3 - 6, "Date of Birth: " + bDate + " (" + str(age) + " years old)")
            if(dDate != "n/a"):
                c.drawString(xIndent, yStart - gap * 4 - 6, "Date of Death: " + dDate)
            g += 2
        else:
            c.drawString(xIndent, yStart - gap * 2, "Address: " + addr)
            c.drawString(xIndent, yStart - gap * 3, "Date of Birth: " + bDate + " (" + str(age) + " years old)")
            if(dDate != "n/a"):
                c.drawString(xIndent, yStart - gap * 4, "Date of Death: " + dDate)
                aSpace = 23
            else:
                aSpace = 11
        c.drawString(300, yStart - gap, "Race: " + race)
        c.drawString(300, yStart - gap * 2, "Phone #: " + phone)
        c.drawString(300, yStart - gap * 3, "Hospital: " + hospitalName)
        if not isAlive:
            c.drawString(300, yStart - gap * 4, "Cause of Death: " + dCause)

        # Allergies
        c.setFont("Helvetica-Bold", 12)
        c.drawString(xLeft, (yStart - gap * g) - 15 - aSpace, "Allergies")
        yTemp = (yStart - gap * (g+1)) - 15 - aSpace

        c.setFont("Helvetica", 7)
        i = 0
        for a in allergyStrings:
            c.drawString(xIndent, yTemp, allergyStrings[i])
            i = i + 1
            yTemp = yTemp - gap
            if yTemp < 70:
                c.showPage()
                yTemp = 790
                pageNum = pageNum + 1
                c.setFont("Helvetica", 12)
                c.drawString(540, 20, "Page " + str(pageNum))
            c.setFont("Helvetica", 7)

        # Diseases
        yTemp = yTemp - 6
        c.setFont("Helvetica-Bold", 12)
        c.drawString(xLeft, yTemp, "Diseases")
        yTemp = yTemp - 10
        if len(diseaseStrings) == 0:
            yTemp = yTemp - gap/2
        if yTemp < 70:
            c.showPage()
            yTemp = 790
            pageNum = pageNum + 1
            c.setFont("Helvetica", 12)
            c.drawString(540, 20, "Page " + str(pageNum))
        c.setFont("Helvetica-Bold", 12)

        i = 0
        yTemp -= 5
        for d in diseaseStrings:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(xIndent, yTemp, diseaseStrings[i])
            c.setFont("Helvetica", 7)

            c.drawString(xIndent + 20, yTemp - 10, "Date Diagnosed: " + diseasedateStrings[i])
            if yTemp < 70:
                c.showPage()
                yTemp = 790
                pageNum = pageNum + 1
                c.setFont("Helvetica", 12)
                c.drawString(540, 20, "Page " + str(pageNum))
            yTemp = yTemp - 25
            i += 1


        # Medication
        yTemp = yTemp - 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(xLeft, yTemp, "Medication")
        yTemp = yTemp - gap
        if len(medicationStrings) == 0:
            yTemp = yTemp - gap/2
        if yTemp < 70:
            c.showPage()
            yTemp = 790
            pageNum = pageNum + 1
            c.setFont("Helvetica", 12)
            c.drawString(540, 20, "Page " + str(pageNum))
        c.setFont("Helvetica-Bold", 12)

        i = 0

        gaptemp = 12
        for m in medicationStrings:
            c.setFont("Helvetica-Bold", 8)
            c.drawString(xIndent, yTemp, medicationStrings[i])
            c.setFont("Helvetica", 7)

            originalstring = "Directions: " + direcStrings[i]

            if len(originalstring) > 150:
                wrap_text = textwrap.wrap(originalstring, width = 150)
                c.drawString(xIndent + 20, yTemp - gap, wrap_text[0])
                if yTemp < 70:
                    c.showPage()
                    yTemp = 790
                    pageNum = pageNum + 1
                    c.setFont("Helvetica", 12)
                    c.drawString(540, 20, "Page " + str(pageNum))
                c.setFont("Helvetica", 7)
                c.drawString(xIndent + 20 + 36, yTemp - gap - 9, wrap_text[1])
                if yTemp < 70:
                    c.showPage()
                    yTemp = 790
                    pageNum = pageNum + 1
                    c.setFont("Helvetica", 12)
                    c.drawString(540, 20, "Page " + str(pageNum))
                c.setFont("Helvetica", 7)
                yTemp = yTemp - 8
                if yTemp < 70:
                    c.showPage()
                    yTemp = 790
                    pageNum = pageNum + 1
                    c.setFont("Helvetica", 12)
                    c.drawString(540, 20, "Page " + str(pageNum))
                c.setFont("Helvetica", 7)
            else:
                c.drawString(xIndent + 20, yTemp - gap, originalstring)
                yTemp = yTemp - 2
                if yTemp < 70:
                    c.showPage()
                    yTemp = 790
                    pageNum = pageNum + 1
                    c.setFont("Helvetica", 12)
                    c.drawString(540, 20, "Page " + str(pageNum))
                c.setFont("Helvetica", 7)

            c.drawString(xIndent + 20, yTemp - gaptemp * 2, "Status: " + activeStrings[i])
            if yTemp < 70:
                c.showPage()
                yTemp = 790
                pageNum = pageNum + 1
                c.setFont("Helvetica", 12)
                c.drawString(540, 20, "Page " + str(pageNum))
            c.setFont("Helvetica", 7)
            c.drawString(xIndent + 20, yTemp - gaptemp * 3, "Start Date: " + medStartStrings[i])
            if yTemp < 70:
                c.showPage()
                yTemp = 790
                pageNum = pageNum + 1
                c.setFont("Helvetica", 12)
                c.drawString(540, 20, "Page " + str(pageNum))
            c.setFont("Helvetica", 7)
            c.drawString(xIndent + 20, yTemp - gaptemp * 4, "End Date: " + endStrings[i])
            if yTemp < 70:
                c.showPage()
                yTemp = 790
                pageNum = pageNum + 1
                c.setFont("Helvetica", 12)
                c.drawString(540, 20, "Page " + str(pageNum))
            c.setFont("Helvetica", 7)
            i = i + 1
            yTemp = (yTemp - gaptemp * 5) - 10
            if yTemp < 70:
                c.showPage()
                yTemp = 790
                pageNum = pageNum + 1
                c.setFont("Helvetica", 12)
                c.drawString(540, 20, "Page " + str(pageNum))
            c.setFont("Helvetica", 7)

        # Shots
        c.setFont("Helvetica-Bold", 12)
        c.drawString(xLeft, yTemp, "Immunizations")
        yTemp = yTemp - gap
        if yTemp < 70:
            c.showPage()
            yTemp = 790
            pageNum = pageNum + 1
            c.setFont("Helvetica", 12)
            c.drawString(540, 20, "Page " + str(pageNum))
        c.setFont("Helvetica", 12)
        i = 0
        c.setFont("Helvetica", 7)
        if not isFHIR:
            for s in range(len(shotStrings)/2):
                c.drawString(xIndent, yTemp, shotStrings[i])
                i = i + 2
                yTemp = yTemp - gap
                if yTemp < 70:
                    c.showPage()
                    yTemp = 790
                    pageNum = pageNum + 1
                    c.setFont("Helvetica", 12)
                    c.drawString(540, 20, "Page " + str(pageNum))
                c.setFont("Helvetica", 7)
        else:
            for s in range(len(shotStrings)):
                c.drawString(xIndent, yTemp, shotStrings[i] + ":  " + shotdateStrings[i][:10])
                i += 1
                yTemp = yTemp - gap
                if yTemp < 70:
                    c.showPage()
                    yTemp = 790
                    pageNum = pageNum + 1
                    c.setFont("Helvetica", 12)
                    c.drawString(540, 20, "Page " + str(pageNum))
                c.setFont("Helvetica", 7)

        yTemp = yTemp - 10
        if yTemp < 70:
            c.showPage()
            yTemp = 790
            pageNum = pageNum + 1
            c.setFont("Helvetica", 12)
            c.drawString(540, 20, "Page " + str(pageNum))

        # Active Problems
        c.setFont("Helvetica-Bold", 12)
        c.drawString(xLeft, yTemp, "Active Problems")
        yTemp = yTemp - gap
        c.setFont("Helvetica", 7)
        i = 1
        for p in range(len(probStrings)/2):
            c.drawString(xIndent, yTemp, probStrings[i])
            yTemp = yTemp - gap
            i = i + 2
            if yTemp < 70:
                c.showPage()
                yTemp = 790
                pageNum = pageNum + 1
                c.setFont("Helvetica", 12)
                c.drawString(540, 20, "Page " + str(pageNum))
            c.setFont("Helvetica", 7)

        c.save()
        recordCount += 1


# check if there are records in the records directory
if firstTime:
    print("Please put medical records into the records directory")

# # search
# # http://code.activestate.com/recipes/578860-setting-up-a-listbox-filter-in-tkinterpython-27/
# class Application(Frame):
#
#     def __init__(self, master=None):
#         Frame.__init__(self, master)
#
#         self.pack()
#         self.create_widgets()
#
#     def callback():
#         print "click"
#
#     # Create main GUI window
#     def create_widgets(self):
#         self.search_var = StringVar()
#         self.search_var.trace("w", lambda name, index, mode: self.update_list()).decode(sys.stdin.encoding)
#         self.entry = Entry(self, textvariable=self.search_var, width=13)
#         self.lbox = Listbox(self, width=45, height=15)
#
#         self.entry.grid(row=0, column=0, padx=10, pady=3)
#         self.lbox.grid(row=1, column=0, padx=10, pady=3)
#
#         # Function for updating the list/doing the search.
#         # It needs to be called here to populate the listbox.
#         self.update_list()
#
#
#     def callback():
#         print "click!"
#
#     def update_list(self):
#         search_term = self.search_var.get().lower().decode(sys.stdin.encoding)
#         # Just a generic list to populate the listbox
#         self.lbox.delete(0, END)
#
#         foundCount = 0
#         found = False
#         i = 0
#         for item in recordNames:
#             if search_term.lower() in searchSet[i]:
#                 found = True
#                 foundCount += 1
#                 self.lbox.insert(END, item)
#             if not found:
#                 for var in searchSet[i]:
#                     if search_term.lower() in var:
#                         self.lbox.insert(END, item)
#                         foundCount += 1
#                         break
#             i += 1
#             found = False
#             # print("Found " + str(foundCount) + " records")

def create_bar_graph(arr, name, title, c, m, y, k):
    d = Drawing(280, 250)
    bar = VerticalBarChart()
    bar.x = 50
    bar.y = 85
    data = [arr]
    bar.data = data
    bar.categoryAxis.categoryNames = title

    bar.bars[0].fillColor = PCMYKColor(c, m, y, k, alpha=85)
    # bar.bars[1].fillColor = PCMYKColor(23, 51, 0, 4, alpha=85)
    bar.bars.fillColor = PCMYKColor(100, 0, 90, 50, alpha=85)

    d.add(bar, '')
    d.save(formats=['pdf'], outDir='.', fnRoot=statsPath + name)

if __name__ == '__main__':
    create_bar_graph(ageDist, "Age_Distribution", ageXAxis, 82, 17, 23, 0)
    create_bar_graph(raceDist, "Race_Distribution", raceXAxis, 0, 90, 17, 0)

# population disease count
diseaseDict = {i:popDiseaseList.count(i) for i in popDiseaseList}
print(diseaseDict)
# **************************************

def search(searchVal):
    foundCount = 0
    ageTemp = [0] * len(ageDist)
    raceTemp = [0] * len(raceDist)
    i = 0
    empty = True
    for s in searchSet:
        if searchVal in searchSet[i]:
            empty = False
            print("\tFound in " + recordNames[i])
            ageTemp[ageGroup[i]] += 1
            raceTemp[raceGroup[i]] += 1
            foundCount += 1
        i += 1
    i = 0
    duplicate = False
    if empty:
        for s in searchSet:
            for var in searchSet[i]:
                if searchVal in var:
                    empty = False
                    if duplicate == False:
                        print("\tFound in " + recordNames[i])
                        ageTemp[ageGroup[i]] += 1
                        raceTemp[raceGroup[i]] += 1
                        foundCount += 1
                        duplicate = True
            duplicate = False
            i += 1
    foundStat = round(float(foundCount) / float(recordCount), 4) * 100
    print("\n\t\"" + searchVal.capitalize() + "\" found in " + str(foundCount) + " record(s) (" + str(foundStat) + "%)")
    wantReport = raw_input("Generate a report? (Y/N) ").lower()
    if wantReport == "y" or wantReport == "yes":
        create_bar_graph(ageTemp, '/search_statistics/' + '"' + searchVal + '"' + "_Age_Distribution", ageXAxis, 82, 17, 23, 0)
        create_bar_graph(raceTemp, '/search_statistics/' + '"' + searchVal + '"' + "_Race_Distribution", raceXAxis, 0, 90, 17, 0)

        print("\t" + "Report will be generated upon quitting")

if not firstTime:
    searchVal = ""
    while searchVal != "quit" :
        searchVal = raw_input('What are you looking for? (Type "quit" to quit) ').lower().decode(sys.stdin.encoding)
        if searchVal != "quit" and searchVal == "":
            print("\tPlease enter an input")
        elif searchVal != "quit":
            search(searchVal)

# # run tkinter search
# root = Tk()
# root.title('Record Search')
# app = Application(master=root)
# app.mainloop()
