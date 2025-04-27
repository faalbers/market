from gics import GICS
from pprint import pp

# https://www.msci.com/our-solutions/indexes/gics
# https://www.spglobal.com/marketintelligence/en/documents/112727-gics-mapbook_2018_v3_letter_digitalspreads.pdf

class GICSM():
    def __init__(self):
        self.definition = GICS().definition
        codes = sorted(self.definition)
        self.__gics_data = {}
        # levelChildren = {0: 'industry_groups', 1: 'industries', 2: 'sub_industries'}
        category_names = {0: 'sector', 1: 'industry_group', 2: 'industry', 3: 'sub_industry'}
        for code in codes:
            level_codes = []
            while len(code) > 0:
                # chump code into first 2 digit groups
                level_code = code[:2]
                if len(level_code) > 0:
                    level_codes.append(level_code)
                code = code[2:]
            current_code = ''
            gics_current = self.__gics_data
            level = 0
            # print()
            # print(level_codes)
            for level_code in level_codes:
                # go through each level and find code and it's data
                current_code += level_code
                # print('\t%s: %s' % (level,current_code))
                code_data = self.definition[current_code]
                # code_name = code_data['name']
                # code_description = code_data['description']

                # add category
                category_name = category_names[level]
                if not category_name in gics_current:
                    gics_current[category_name] = {}
                gics_current = gics_current[category_name]

                # add name and data
                if not code_data['name'] in gics_current:
                    gics_current[code_data['name']] = {}
                    gics_current[code_data['name']]['code'] = current_code
                    if 'description' in code_data:
                        gics_current[code_data['name']]['description'] = code_data['description']
                    gics_current[code_data['name']]['categories'] = {}
                gics_current = gics_current[code_data['name']]['categories']
                level += 1
        return
        levelChildren = {0: 'industry_groups', 1: 'industries', 2: 'sub_industries'}
        for code in codes:
            levelCodes = []
            while len(code) > 0:
                levelCode = code[:2]
                if len(levelCode) > 0:
                    levelCodes.append(levelCode)
                code = code[2:]
            currentCode = ''
            gicsCurrent = self.__gics_data
            level = 0
            for levelCode in levelCodes:
                currentCode += levelCode
                codeData = self.definition[currentCode]
                levelName = codeData['name']
                if not levelName in gicsCurrent:
                    gicsCurrent[levelName] = {}
                gicsCurrent[levelName]['code'] = currentCode
                if 'description' in codeData:
                    gicsCurrent[levelName]['description'] = codeData['description']
                
                if level in levelChildren:
                    childrenName = levelChildren[level]
                    if not childrenName in gicsCurrent[levelName]:
                        gicsCurrent[levelName][childrenName] = {}
                    gicsCurrent = gicsCurrent[levelName][childrenName]
                
                level += 1

    def print_hierarchy(self):
        GICSM.__print_hierarchy(self.__gics_data, 0)

    @staticmethod
    def __print_hierarchy(data, level):
        tab = '\t'
        tabs = tab * level
        for category, category_data in data.items():
            # print('%s%s:' % (tabs, category))
            for name, name_data in category_data.items():
                print('%s%s: %s (%s)' % (tabs, name, name_data['code'], category))
                GICSM.__print_hierarchy(name_data['categories'], level + 1)
