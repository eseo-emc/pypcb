import inspect

def converter(theFunction):
    theFunction.isConverter = None
    return theFunction
    
def backConverter(theFunction):
    assert theFunction.__name__.endswith('ToEssence')
    return theFunction

class Convertible(object):
    def __init__(self,essence=None,**kwargs):
        self.derivedForms = []
        for (attributeName,attribute) in inspect.getmembers(self):
            if hasattr(attribute,'isConverter'):
                self.derivedForms += [attributeName]

        if type(essence) is not type(None):
            self.essence = lambda : self.normalise(essence)
        for argument,value in kwargs.iteritems():
            assert hasattr(self,argument)
            setattr(self,argument,value)

    def essence(self):
        preferredForm = self.determinationForms()[0]
        backConverter = getattr(self,preferredForm+'ToEssence')
        return backConverter(getattr(self,preferredForm))

    def normalise(self,rawEssence):
        return rawEssence

    def determinationForms(self):
        values = []
        for form in self.derivedForms:
            assert hasattr(self,form), '{self} should have attribute {form}'.format(self=self,form=form)
            formAttribute = getattr(self,form)            
            
            if not(callable(formAttribute)):
                values += [form]
                    
        return values
