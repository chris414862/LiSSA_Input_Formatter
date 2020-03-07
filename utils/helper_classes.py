class lissa_annotation():
    '''
    Class representing an annotation for the LiSSA classifier
    '''

    def __init__(self, class_name='', method_name='', parameters=[], returns='', category='', origin=''
                 , source_or_sink=""):
        if class_name == '':
            self.class_name = self.get_class_name(method_name)
        else:
            self.class_name = class_name

        name_toks = method_name.split(".")
        self.method_name = name_toks[len(name_toks)-1] #last element

        self.parameters = parameters
        self.returns = returns
        self.category = category
        self.source_or_sink = source_or_sink
        self.origin = origin

    def get_class_name(self, full_name):
        toks = full_name.split(".")
        if len(toks) == 0:
            return ""
        return ".".join(toks[:len(toks)-1])

    def to_string(self):
        return "<"+self.class_name+": "+self.returns.split(".")[-1]+" "+self.method_name+"("\
               +",".join([p.split(".")[-1] for p in self.parameters ])+")>|||"\
               +self.origin+"|||"+self.source_or_sink +'|||'+self.category


class documentation():
    '''
    This did not end up being needed, but will probably be of use in the feature extraction module to be written later
    '''
    def __init__(self, meth_doc="", param_docs={}, ret_doc=()):
        self._meth_doc=meth_doc(meth_doc)
        self._param_docs=param_docs
        self._ret_doc=ret_doc

    @property
    def meth_doc(self) -> str:
        return self._meth_doc

    @meth_doc.setter
    def meth_doc(self, doc):
        if type(doc) != str:
            raise ValueError("Method documentation should be a string")
        self._meth_doc = doc

    @property
    def param_docs(self) -> list:
        return self._param_docs

    @param_docs.setter
    def param_docs(self, docs):
        if type(docs) != list:
            raise ValueError("Parameter documentation should be a list of 3-tuples - (param name, str of type, doc)")
        self._param_docs = docs

    @property
    def ret_doc(self) -> tuple:
        return self._ret_doc

    @ret_doc.setter
    def meth_doc(self, tup):
        if type(tup) != tuple:
            raise ValueError("Return val documentation should be a tuple - (str of type, doc)")
        self._ret_doc = tup
