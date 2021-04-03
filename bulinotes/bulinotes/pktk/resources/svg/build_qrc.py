#!/usr/bin/python3

# Build .qrc files from SVG files 


import os.path
import re

CURRENT_PATH=os.path.realpath(os.path.dirname(__file__))

CONFIG={
        'LINKS':{
                '32dp':          'pktk/images/normal',
                '32dp-disabled': 'pktk/images/disabled',
                'white/32dp':          'pktk/images-white/normal',
                'white/32dp-disabled': 'pktk/images-white/disabled'
            },
        
        'TARGETS':{
                'FILES': {
                        'dark': 'dark_icons.qrc',
                        'light': 'light_icons.qrc'
                    },
                'PATH': CURRENT_PATH
            }
    }
 

def main():
    """main process"""
    
    for fileKey in CONFIG['TARGETS']['FILES']:
        fileContent=['<RCC>']
        
        for srcLink in CONFIG['LINKS']:
            fileContent.append(f'''  <qresource prefix="{CONFIG['LINKS'][srcLink]}">''')
            
            directoryToProcess=os.path.join(CURRENT_PATH, fileKey, srcLink)
            
            directoryContent=os.listdir(directoryToProcess)
            
            for fileName in directoryContent:
                fullPathFileName=os.path.join(directoryToProcess, fileName)
                
                if os.path.isfile(fullPathFileName):
                    fName=re.search("(.*)\.svg$", fileName)
                    
                    if fName:
                        fileContent.append(f'    <file alias="{fName.groups()[0]}">{fileKey}/{srcLink}/{fileName}</file>')
            
            fileContent.append(f'  </qresource>')
            
        fileContent.append('</RCC>')
        
        targetFileName=os.path.join(CONFIG['TARGETS']['PATH'], CONFIG['TARGETS']['FILES'][fileKey])
        print(targetFileName)
        with open(targetFileName, 'w') as fHandle:
            fHandle.write("\n".join(fileContent))
            
            

if __name__ == "__main__":
    main()
