import datetime

class Age:
    """A class to store the age data from a speaker."""
    def __init__(self, ageStr = None):
        self.decimal = None
        self.years = None
        self.months = None
        self.days = None
        self.hours = None
        self.minutes = None
        self.seconds = None

        if not ageStr is None:
            self.parseAge(ageStr)

    def parseAge(self, ageStr):
        # P25Y0M0DT0H0M0S
        if type(ageStr) is int or type(ageStr) is float:
            self.decimal = ageStr
            d = datetime.timedelta(days=(self.decimal * 365))
            self.years = int(d.days / 365)
            self.months = int((d.days - (self.years * 365)) / 30)
            h = d.seconds / 60 / 60
            self.hours = int(h)
            m = (h - self.hours) * 60
            self.minutes = int(m)
            self.seconds = int(d.seconds - (self.hours * 60 * 60) - (self.minutes * 60))
        elif ageStr[0] == "P":
            ageStr = ageStr[1:]
            ageList = ageStr.split("T")
            ageDate = ageList[0]

            # Not all age data has time specified, if it does not, ignore.
            if len(ageList) > 1:
                # Process the time from the age.
                ageTime = ageList[1]
                temp = ageTime.split("H")
                self.hours = int(temp[0][:])
                temp = temp[1].split("M")
                self.minutes = int(temp[0][:])
                temp = temp[1].split("S")
                self.seconds = int(temp[0][:])
            else:
                # If there is no time data, set all to 0.
                self.hours = 0
                self.minutes = 0
                self.seconds = 0

            # Process the date from the age.
            temp = ageDate.split("Y")
            self.years = int(temp[0][:])
            temp = temp[1].split("M")
            if temp[0] == "":
                self.months = 0
            else:
                self.months = int(temp[0][:])

            # Not all age data has days specified.
            if len(temp) > 1:
                temp = temp[1].split("D")
                if temp[0] == "":
                    self.days = 0
                else:
                    self.days = int(temp[0][:])
            else:
                self.days = 0

            # Turn the individual fields into a decimal age.
            self.decimal = self.years + (self.months / 12) + (self.days / 365.25) + (self.hours / 8760) + \
                           (self.minutes / 525600) + (self.seconds / 525600 * 60)