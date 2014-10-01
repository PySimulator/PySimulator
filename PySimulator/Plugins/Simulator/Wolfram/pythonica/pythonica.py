import mathlink as _ml
import time as _time

__author__="""\n""".join(['Benjamin Edwards (bedwards@cs.unm.edu)'])

#    Copyright (C) 2012
#    Benjamin Edwards
#    All rights reserved.
#    BSD license

# Packets that signify incoming tokens
_incoming_token = [_ml.RETURNPKT,
                   _ml.RETURNEXPRPKT,
                   _ml.DISPLAYPKT,
                   _ml.DISPLAYENDPKT,
                   _ml.RESUMEPKT,
                   _ml.RETURNTEXTPKT,
                   _ml.SUSPENDPKT,
                   _ml.MESSAGEPKT]

#identity function for anything to strings
_id_to_mathematica = lambda x: str(x)

#Convert a float to a string for mathematica
def _float_to_mathematica(x):
    return ("%e"%x).replace('e','*10^')

#Convert a complex to a string for mathematica
def _complex_to_mathematica(z):
    return 'Complex' + ('[%e,%e]'%(z.real,z.imag)).replace('e','*10^')

#convert some type of container to a string for matheatica
def _iter_to_mathematica(xs):
    s = 'List['
    for x in xs:
        s += _python_mathematica[type(x)](x)
        s += ','
    s = s[:-1]
    s+= ']'
    return s

#Convert a string to a mathematica string
def _str_to_mathematica(s):
    return '\"%s\"'%s

#Dictionary for type conversions.
_python_mathematica = {bool:_id_to_mathematica,
                       type(None):_id_to_mathematica,
                       int:_id_to_mathematica,
                       float:_float_to_mathematica,
                       long:_id_to_mathematica,
                       complex:_complex_to_mathematica,
                       iter:_iter_to_mathematica,
                       list:_iter_to_mathematica,
                       set:_iter_to_mathematica,
                       xrange:_iter_to_mathematica,
                       str:_str_to_mathematica,
                       tuple:_iter_to_mathematica,
                       frozenset:_iter_to_mathematica}

#Take a string from mathematica and try to make it into a python object
#This could likely be written better and in the future could include
#methods for other functional conversions
def _mathematica_str_python(s):
    if s == 'Null' or s is None:
        return None
    try:
        val = int(s)
    except ValueError:
        try:
            val = float(s)
        except ValueError:
            try:
                val = float(s.replace('*10^','e'))
            except ValueError:
                val = None
    # Some sort of Number, so return it NEED TO ADD COMPLEX and Rational
    if val is not None:
        return val
    val = {}
    s = s.replace(" ","").replace('{','List[').replace('}',']')
    open_brack = s.find("[")
    #Some String not a function Call, likely rational,complex,list or symbol
    if open_brack == -1:
        div = s.find('/')
        if div != -1:
            try:
                num = _mathematica_str_python(s[:div])
                den = _mathematica_str_python(s[div+1:])
                if num/den == float(num)/den:
                    return num/den
                else:
                    return float(num)/den
            except TypeError:
                val = s
        im = s.find('I')
        if im == -1:
            val = s
        else:
            plus = s.find('+')
            times = s.find('*I')
            if plus != -1:
                if times != -1:
                    try:
                        return complex(_mathematica_str_python(s[:plus]),
                                       _mathematica_str_python(s[plus+1:times]))
                    except TypeError:
                        val = s
                else:
                    try:
                        return complex(_mathematica_str_python(s[:plus]),1)
                    except TypeError:
                        val = s
            else:
                if times != -1:
                    try:
                        return complex(0,_mathematica_str_python(s[:times]))
                    except TypeError:
                        val = s
                else:
                    return complex(0,1)
        return val
    func = s[:open_brack]
    num_open_brack = 1
    val[func] = [] 
    last_comma = open_brack
    for i in range(open_brack+1,len(s)):
        if s[i] == ',' and num_open_brack == 1:
            val[func].append(_mathematica_str_python(s[last_comma+1:i]))
            last_comma = i
        elif s[i] == '[':
            num_open_brack += 1
        elif s[i] == ']':
            if num_open_brack > 1:
                num_open_brack -= 1
            elif num_open_brack == 1:
                val[func].append(_mathematica_str_python(s[last_comma+1:len(s)-1]))
            else:
                raise Exception("Unbalanced Brackets")
    if func == 'List':
        return val['List']
    elif func == 'Complex':
        return complex(val['Complex'][0],val['Complex'][1])
    elif func == 'Rational':
        return float(val['Rational'][0])/val['Rational'][1]
    else:
        return val

#Searches Mathematica string of type 'InputForm' for things to plot
def _find_plot_strings(s):
    ps = []
    for g_func in ['Graphics[','Graphics3D[','Image[','Grid[']:
        while True:
            graph_start = s.find(g_func)
            if graph_start == -1:
                break
            num_brack = 1
            for i in range(graph_start+len(g_func),len(s)):
                if s[i] == '[':
                    num_brack += 1
                elif s[i] == ']':
                    if num_brack == 1:
                        ps.append(s[graph_start:i+1])
                        break
                    else:
                        num_brack -= 1
            s = s.replace(s[graph_start:i+1],'')
    return ps


#Exception
class PythonicaException(Exception):
    pass

class Pythonica(object):
    """
    Base class for Mathematica Communication.

    Creates a link to a Mathematica Kernel and stores information needed
    communication

    Parameters
    ----------
    name : string
      String to launch mathlink.
    mode : string
      Sting for mode to launch mathlink
    timeout : int
      Time to give Mathematica to start the kernel
    debug : Bool
      Whether to print debug information
    plot_dir : string
      Directory to store plots
    plot_size : tuple of 2 ints
      Tuple containing plot size in pixels. If None let's Mathematica decide
      what size to make things
    plot_format : string
      Format for plots, default to 'png'. 'bmp', 'svg', and 'jpeg' tested and
      seem to work.
    output_prompt : string
      Whether to print output prompts reported from Mathematica
    input_prompt : string
      Whether to print input prompts reported from Mathematica

    Examples
    --------
    >>> import pythonica
    >>> m = pythonica.Pythonica()
    >>> m.eval('Mean[{1,2,3}]')
    '2'
    """


    def __init__(self,
                 name='math -mathlink',
                 mode='launch',
                 timeout=1,
                 debug=False,
                 plot_dir=None,
                 plot_size=None,
                 plot_format='png',
                 output_prompt=False,
                 input_prompt=False):
        import sys
        self._env = _ml.env()
        self.mathematicaversion = "10.0"
        sys.argv.extend(['-linkname', "C:\\Program Files\\Wolfram Research\\Mathematica\\" + self.mathematicaversion + "\\Math.exe -mathlink"])

        self.kernel = self._env.openargv(sys.argv)
       # print type(self.kernel)
        self.kernel.connect()
        self.debug=debug
        self.plot_dir = plot_dir
        self.plot_num = 0
        self.last_python_result=None
        self.last_str_result=None
        self.plot_size = plot_size
        self.plot_format = plot_format
        self.output_prompt = output_prompt
        self.input_prompt = input_prompt
        self.last_error = None
        _time.sleep(timeout)
        if not self.kernel.ready():
            raise PythonicaException("Unable to Start Mathematica Kernel")
        else:
            packet = self.kernel.nextpacket()
            if self.debug:
                print _ml.packetdescriptiondictionary[packet]
            if packet == _ml.INPUTNAMEPKT:
                self.kernel.getstring()

    def eval(self,expression,make_plots=True,output_type='string',str_format='input'):
        """
        Evaluate a string in the Mathematica Kernel

        Evalutes the string 'expression' in Mathematica.

        Parameters
        ----------
        expression: string
          Expression to be evaluated
        make_plots: boolean
          Whether to produce plots, plot_dir must not be None
        output_type: string
          Whether to output a string or a python object, must be either
          'string' or 'python'
        str_format: string
          How to format the string if output_type='string'. If 'input' will
          produce a string which can be used as Mathematica Input. If 'tex'
          will produce valid tex. If 'plain' will produce whatever plain text
          mathematica would produce.

        Returns
        -------
        String or python object.

        Raises
        ------
        PythonicaException

        Examples
        --------

        >>> m.eval('D[Log[x],x]')
        'x^(-1)'
        >>> m.eval('Mean[{1,2,3,4}]',output_type='python')
        2.5
        >>> m.eval('D[Log[x],x]',str_output='tex')
        '\\\\frac{1}{x}'
        >>> print m.eval('D[Log[x],x]',str_output='plain')
        1
        -
        x

        See Also
        --------
        README.rst
        """
        self.last_python_result=None
        self.last_str_result=None
        self.last_error=None
        if str_format=='tex':
            expression = 'ToString[' + expression+',TeXForm]'
        elif str_format=='input':
            expression = 'ToString[' + expression + ',InputForm]'
        elif str_format=='plain':
            pass
        else:
            raise PythonicaException("String Format must be 'tex', 'input', or 'plain'")
        self.kernel.putfunction("EnterTextPacket",1)
        self.kernel.putstring(expression)
        self.__parse_packet()
        str_result = self.last_str_result
        if self.last_error is not None:
            raise PythonicaException(self.last_error.decode('string_escape'))
        if make_plots and self.plot_dir is not None:
            plot_exp = _find_plot_strings(str_result)
            for s in plot_exp:
                filename='\"%s/pythonica_plot_%i.%s\"'%(self.plot_dir,self.plot_num,self.plot_format)
                if self.plot_size is None:
                    self.eval('Export[%s,%s];'%(filename,s),make_plots=False,str_format='plain')
                else:
                    (w,h) = self.plot_size
                    self.eval('Export[%s,%s,ImageSize->{%i,%i}];'%(filename,s,w,h),make_plots=False,str_format='plain')
                self.plot_num += 1
        if str_format == 'plain' and str_result is not None:
            str_result = str_result.decode('string_escape')
        self.last_str_result = str_result
        if output_type == 'python':
            self.last_python_result = _mathematica_str_python(str_result)
            return self.last_python_result
        elif output_type == 'string':
            self.last_python_result = None
            if str_result == 'Null':
                return None
            else:
                return str_result
        else:
            raise PythonicaException("Output Type must be either 'python' or 'string'(default)")

    def push(self, name, value):
        """
        Push python object to Mathematica Kernel.

        Can make some conversions of python objects to Mathematica. See
        README.rst for more information.

        Parameters
        ----------
        name : string
          Name for value in Mathematica Kernel
        value : python object
          Object to be pushed to Mathematica Kernel

        Returns
        -------
        None

        Raises
        ------
        PythonicaException: If the object cannot be converted

        Examples
        --------

        >>> m.push('l',[1,2,3])
        >>> m.eval('l2 = 2*l;')
        >>> m.pull('l2')
        [2,4,6]
        """

        convert_function = _python_mathematica.get(type(value),-1)
        if convert_function is -1:
            raise PythonicaException("Could not convert %s to Mathematica Object"%type(value))
        s = 'Set[%s,%s];'%(name,convert_function(value))
        self.eval(s,make_plots=False)

    def pull(self,name):
        """
        Return a Mathematica Object to the python environment.

        Parameters
        ---------
        name: string
          Name to retrieve

        Returns
        -------
        python object:
          Depending on type will be converted. See README.rst for more info

        Examples
        --------

        >>> m.eval('X = List[1,2,3,4]')
        >>> m.pull('X')
        [1,2,3,4]
        """
        res = self.eval(name,make_plots=False)
        return _mathematica_str_python(res)

    def __parse_packet(self):
        if self.debug:
            print("in __parse_packet")
        packet = self.kernel.nextpacket()
        if self.debug:
            print _ml.packetdescriptiondictionary[packet]
        if packet == _ml.INPUTNAMEPKT:
            if self.input_prompt:            
                print(self.kernel.getstring())
            else:
                self.kernel.getstring()
            return None 
        elif packet == _ml.OUTPUTNAMEPKT:
            if self.output_prompt:
                print(self.kernel.getstring())
            else:
                self.kernel.getstring()
            self.__parse_packet()
        elif packet == _ml.MESSAGEPKT:
            if self.last_error is None:
                self.last_error = self.kernel.getstring()
            else:
                self.last_error += "\t" + self.kernel.getstring()
            self.__parse_token(packet)
            self.__parse_packet()
        elif packet == _ml.TEXTPKT:
            self.last_error += self.kernel.getstring()
            self.__parse_packet()
        elif packet == _ml.SYNTAXPKT:
            self.kernel.getstring()
            self.__parse_packet()
        elif packet in _incoming_token:
            if self.debug:
                print("Going to Parse Token")
            self.last_str_result = self.__parse_token(packet).replace(r'\\\012','').replace(r'\012>   ','')
            self.__parse_packet()
        else:
            raise PythonicaException("Unknown Packet %s"%_ml.packetdescriptiondictionary[packet])


    def __parse_token(self,packet):
        if self.debug:
            print("In Parse Token")
        try:
            token = self.kernel.getnext()
            if self.debug:
                print _ml.tokendictionary[token]
        except _ml.error, e:
            raise PythonicaException("Got Error Token: %s"%e)
        if token == _ml.MLTKSTR:
            return self.kernel.getstring()
        else:
            raise PythonicaException("Unknown Token %i",token)

    def __del__(self):
        self.kernel.close()
