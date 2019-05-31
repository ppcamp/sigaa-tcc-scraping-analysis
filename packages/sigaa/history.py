from packages.sigaa.base import sigaaBase
from packages.sigaa.grid import GridScraping
# ==============================================================
# History
# ==============================================================


class HistoryScraping(sigaaBase):

    def __init__(self, **kwargs):
        sigaaBase.__init__(self, **kwargs)

        # History
        self._history = {}
        self._yearActualPeriod = None
        self._yearInPeriod = None
        self._courseName = None
        self._studentId = None

    def get_History(self):
        """
        Set the history. This method assumes that
        you did _login with student account.\n
        You can pass argument 'xml' to generate file when finish.

        Parameters
        """
        # clean string
        import re as regex

        # Need to download pdf's file only to search
        # for Getting grid
        import textract

        # Header's info
        try:
            self._courseName = self._chrome_webdriver.find_element_by_css_selector(
                '#agenda-docente > table > tbody > tr:nth-child(2) > td:nth-child(2)').text
            self._studentId = self._chrome_webdriver.find_element_by_css_selector(
                '#agenda-docente > table > tbody > tr:nth-child(1) > td:nth-of-type(2)').text
            self._yearInPeriod = self._chrome_webdriver.find_element_by_css_selector(
                '#agenda-docente > table > tbody > tr:nth-child(6) > td:nth-child(2)').text
            self._yearActualPeriod = self._chrome_webdriver.find_element_by_css_selector(
                '#info-usuario > p.periodo-atual > strong').text

            nameFile = self._folder_xmlFiles + \
                'historico_{}.xml'.format(self._studentId)

            # If file exist, cancel search
            if self.fileExist(nameFile):
                self._logFile.write(
                    '[get_History]: Failure! File already exist')
                return False
            else:
                self._logFile.write('[get_History]->HeadersInfo: Success!\n')
        except Exception as ex:
            self._logFile.write('[get_History]->HeadersInfo: Failure! {}: {}!\n'.format(
                type(ex).__name__, ex.args))

        # Create basis with (Nome, sigla, CH, Turma)
        try:
            self._chrome_webdriver.get(self._url_discipline)
            soup = self.BeautifulSoup(
                self._chrome_webdriver.page_source, 'html5lib')
            soup = soup.find('table', class_='listagem')

            for i in soup.find_all('tr'):  # , class_='linhaPar'):
                # escape from tr' that are not importants to us
                if i.get('class') is None or i.get('class')[0] == 'destaque':
                    continue
                itsigla = i.find('td').text
                itnome = itsigla[itsigla.find(' - ') + 3:]
                itsigla = itsigla[:itsigla.find(' -')]
                periodo = (i.find_previous('td', class_='periodo').text)
                itturma = i.find_next('td').find_next('td').text
                ch = (i.find_next('td').find_next(
                    'td').find_next('td')).text[:-1]

                if (periodo not in self._history):
                    self._history[periodo] = {
                        itsigla: {
                            'nome': itnome,
                            'turma': itturma,
                            'ch': ch
                        }
                    }
                else:
                    self._history[periodo].update({
                        itsigla: {
                            'nome': itnome,
                            'turma': itturma,
                            'ch': ch
                        }
                    })

                # adicionando DISCIPLINA do bloco
                if itsigla[-1] == '1' and itsigla[-2] == '.':
                    self._history[periodo].update({
                        itsigla[:-2]: {
                            'nome': itnome,
                        }
                    })

            self._logFile.write('[get_History]->Basis: Success!\n')
        except Exception as ex:
            self._logFile.write('[get_History]->Basis: Failure! {}: {}!\n'.format(
                type(ex).__name__, ex.args))

        # Adding info to history (notas, faltas, situacao)
        try:
            # access notes with func cmItemMouseup
            self._chrome_webdriver.get(self._url_default)
            # script found that generates the page
            js_script = "try{cmItemMouseUp('menu_form_menu_discente_j_id_jsp_275447739_49_menu',1);}catch(e){}"
            self._chrome_webdriver.execute_script(js_script)
            soup = self.BeautifulSoup(
                self._chrome_webdriver.page_source, 'html5lib')

            # mont
            for i in soup.find_all_next('tr', class_='linha'):
                sigla = i.find_next('td')
                resultado = sigla.find_next('td').find_next(
                    'td').find_next('td').find_next('td').find_next('td')
                faltas = resultado.find_next('td')
                situacao = faltas.find_next('td')

                sigla = sigla.text.replace(' ', '')
                sigla = regex.sub('[\n\t]', "", sigla)

                resultado = resultado.text.replace(' ', '')
                resultado = regex.sub('[\n\t]', "", resultado)

                faltas = faltas.text.replace(' ', '')
                faltas = regex.sub('[\n\t]', "", faltas)

                situacao = situacao.text.replace(' ', '')
                situacao = regex.sub('[\n\t]', "", situacao)

                periodo = regex.sub(r'\s', '', i.find_previous('caption').text)

                # considera apenas materias (exclui resultado dos blocos)
                if (sigla in self._history[periodo]):
                    self._history[periodo][sigla].update({
                        'resultado': resultado,
                        'faltas': faltas,
                        'situacao': situacao
                    })

            self._logFile.write('[get_History]->InfosHistory: Success!\n')
        except Exception as ex:
            self._logFile.write('[get_History]->InfosHistory: Failure! {}: {}!\n'.format(
                type(ex).__name__, ex.args))

        # check if file (pdf) exist in temp files, otherwise download it
        nameFile = self._folder_temp + \
            'historico_{}.pdf'.format(self._studentId)
        if not self.fileExist(nameFile):
            self._chrome_webdriver.get(self._url_default)
            # script found that download the pdf file
            js_script = "try{cmItemMouseUp('menu_form_menu_discente_j_id_jsp_275447739_49_menu',4);}catch(e){}"
            self._chrome_webdriver.execute_script(js_script)

        # PDF (Getting grid)
        try:
            pt = textract.process(
                '{}historico_{}.pdf'.format(
                    self._folder_temp, self._studentId),
                method='pdftotext'
            )
            pt = pt.decode("UTF-8")
            pt = str(pt)
            pt = pt.split('\n')
            n = []

            for i in pt:
                if not i.strip():
                    continue
                else:
                    n.append(i)
            pt = '\n'.join(n)

            search = pt.find('Currículo:\n') + 11
            self.grade = ''.join(
                [i for i in pt[search:pt.find('\n', search)] if i.isdigit()])
            # search = pt.find('Período Letivo Atual:\n') + 22
            # self._yearActualPeriod = pt[search:pt.find('\n', search)]

            self._logFile.write('[get_History]->PDF: Success!\n')
        except Exception as ex:
            self._logFile.write('[get_History]->PDF: Failure! {}: {}!\n'.format(
                type(ex).__name__, ex.args))

        # GENERATE XML
        # if len(argv) > 0:
            # if argv[0] == 'xml':
            # self.xml_History()

    def xml_History(self):
        """
        Generate XML history file

        Example
        -------
        >> xml_History() # It creates a xml file, saving all infos.
        """
        # XML
        from xml.etree import ElementTree as ET

        nameFile = self._folder_xmlFiles + \
            'historico_{}.xml'.format(self._studentId)

        # increase every six months
        def aplus(j):
            def incrementyear(s): return (str(int(s[:-2]) + 1) + '.1')
            def incrementsem(s): return (s[:-1] + '2')
            return (incrementyear(j) if j[-1] == '2' else incrementsem(j))

        # removed, search in grid
        # repeat function with no iterator used
        # these codes above is only need to convert
        # 7 to 2019.1
        # nano = self._yearInPeriod # Periodo de entrada '2016.1'
        # for _ in range(int(self._yearActualPeriod)-1): # period '7' → ERRO none in yearActualPeriod
        #    nano = aplus(nano)
        # change to show in style 20XX.Y instead of K
        #self._yearActualPeriod = nano

        if not self.fileExist(nameFile):
            root = ET.Element('HistoricoCurricular')

            ET.SubElement(root, 'Curso').text = self._courseName
            ET.SubElement(root, 'Grade').text = self.grade
            ET.SubElement(root, 'Matricula').text = self._studentId
            ET.SubElement(root, 'AnoPeriodoInicial').text = self._yearInPeriod
            ET.SubElement(
                root, 'AnoPeriodoAtual').text = self._yearActualPeriod

            fstLevel = ET.SubElement(root, 'Semestre')

            # used to calc frequency
            def freq(c, s): return str(round((int(c)-int(s))/int(c)*100))

            semestre = self._yearInPeriod
            while semestre != self._yearActualPeriod:  # Do ...while
                sndLevel = ET.SubElement(fstLevel, 'A{}'.format(semestre))

                for sigla in self._history[semestre]:
                    trdLevel = ET.SubElement(sndLevel, 'Disciplina')
                    ET.SubElement(
                        trdLevel, 'Nome').text = self._history[semestre][sigla]['nome']

                    ET.SubElement(trdLevel, 'Sigla').text = sigla

                    if 'ch' in self._history[semestre][sigla]:
                        ET.SubElement(trdLevel, 'Frequencia').text = freq(
                            self._history[semestre][sigla]['ch'],
                            self._history[semestre][sigla]['faltas'])
                        ET.SubElement(
                            trdLevel, 'CH').text = self._history[semestre][sigla]['ch']

                    ET.SubElement(
                        trdLevel, 'Nota').text = self._history[semestre][sigla]['resultado']

                    ET.SubElement(
                        trdLevel, 'Situacao').text = self._history[semestre][sigla]['situacao']

                semestre = aplus(semestre)

            try:
                tree = ET.ElementTree(root)
                tree.write(nameFile)
                self._logFile.write('[xml_History]: Success!\n')
            except Exception as ex:
                self._logFile.write('[xml_History]: Failure! {}: {}\n'.format(
                    type(ex).__name__, ex.args))
        else:
            self._logFile.write('[xml_History]: Failure! File already exist\n')

    def diagram_History(self):
        nameFile = self._folder_xmlFiles + self._courseCode + '.xml'
        # If grid doesn't exist, download it
        if not self.fileExist(nameFile):
            searchGrid = GridScraping()
            searchGrid.login(user=self._userName, password=self._userPsswd)
            searchGrid.set_codCurso(self._courseCode)
            searchGrid.get_Grid()
            searchGrid.xml_Grid()
            searchGrid.quit_webdriver()

        # Construct a tree with xml grid
        # XML parser
        import xml.etree.ElementTree as ET
        from os.path import abspath as abs
        from graphviz import Digraph

        # Construct a tree with xml grid
        root = ET.parse(nameFile).getroot()
        nameFile = self._studentId + '.dot'  # 2016001942.dot
        # Setting up digraph plot
        graphDotOutput = Digraph(
            engine='neato',  # force position
            name=nameFile,
            filename=nameFile,
            directory=abs(''),
            format='png',
            graph_attr={
                # 'concentrate': 'true',
                'rankdir': 'BT',
                'overlap': 'scale',  # force position
                # splines → polyline, ortho, true/spline, curved
                'splines': 'ortho',  # edge uppon vertix
                # 'margin': '0.5,0.5',
                'sep': '0.5',
            },
            node_attr={
                'pad':'1',
                'nodesep':'2',
                'ranksep':'2'
            }
        )

        # edge pre color vector
        colorVectorEdge = [
            '#FA5F6E', '#FA3246', '#FA253B', '#FA142B', '#BD1C32',
            '#BD0D25', '#AF0019', '#850014', '#840019', '#BB0019'
        ]

        auxX = ''
        incX = -1
        incY = None

        includedNodes = set()

        # Loop for nodes
        for disciplinas in root.findall('Disciplinas/'):
            # Searching for Disciplinas
            for disciplina in disciplinas.findall('.'):
                # Creating vertix
                if (auxX != disciplina.find('Periodo').text):
                    auxX = disciplina.find('Periodo').text
                    incX += 1
                    incY = 0
                if (auxX == 'Optativa'):
                    continue

                auxSigla = disciplina.find('Sigla').text
                nodeColor = '#BDC3C7'  # Wet asphalt default color

                # Percorre, procurando a disciplina
                for itPeriodo, _ in reversed(list(self._history.items())):
                    # skip if don't find in dict
                    if auxSigla not in self._history[itPeriodo]:
                        continue
                    situacaoMateria = self._history[itPeriodo][auxSigla]['situacao']
                    if (situacaoMateria == 'APROVADO'):
                        nodeColor = '#2ECC71' # EMERALD
                    elif (situacaoMateria == 'REPROVADO'):
                        nodeColor = '#E74C3C' #ALIZARIN
                    elif (situacaoMateria == '--'):
                        nodeColor = '#9B59B6' # Amethyst

                strPos = '{0:.3}'.format(str(incX)) + ',' + "-{}!".format(incY)

                graphDotOutput.node(
                    auxSigla,
                    auxSigla,
                    color='none',
                    style='filled',  # 'striped',
                    shape='rectangle',
                    fillcolor='{}'.format(nodeColor),
                    pos=strPos,
                    **{  # Node atributes fixed size
                        'fixedsize': 'true',
                        'width': '2',
                        'height': '1'
                    }
                    # len='0.5'
                    # weight='.5',
                )
                includedNodes.add(auxSigla)
                incY += 1

                # Creating edges
                for pre in disciplina.findall('PreRequisitoTotal/Sigla'):
                    auxPre = pre.text
                    if auxPre in includedNodes:
                        graphDotOutput.edge(
                            auxPre, auxSigla, color=colorVectorEdge[int(auxX)-1])

            # end disciplina loop
        graphDotOutput.render(view=True)
