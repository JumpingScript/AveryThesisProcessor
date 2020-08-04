from .age import Age

class Speaker:
    """A class to store information about a speaker."""
    def __init__(self, sid = None, role = None, name = None, sex = None, age = None, language = None):
        self.sid = sid
        self.role = role.replace("_", " ")
        self.name = name
        self.sex = sex
        self.language = language
        self.adult = False
        self.sibling = False

        if not age is None:
            self.age = Age(age)
        else:
            self.age = None

        if self.age.decimal >= 18:
            self.adult = True

        if self.sid == "BRO" or self.sid == "SIS":
            self.sibling = True

    def checkSpeaker(self, speakerData):
        """Checks to see if a Speaker is the same as this Speaker."""
        if speakerData.role == self.role\
                and speakerData.name == self.name\
                and speakerData.age.decimal == self.age.decimal\
                and speakerData.sex == self.sex:
            return True
        else:
            return False