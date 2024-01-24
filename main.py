import sys
import re
import requests as req
import os
import math

from bs4 import BeautifulSoup

__args__ = []

for i in range(1, len( sys.argv )):
    __args__.append( sys.argv[i] )

def arg_str( key : str , default = None ):

    global __args__

    for index , arg in enumerate( __args__ ):
        if arg == key:

            if index == len( __args__ ) - 1:
                raise Exception("arg %s doesn't have value" % ( key ))

            value = __args__[index + 1]

            del __args__[ index : index + 2 ]

            return value

    if not default is None:
        return default

    raise Exception("arg %s doesnt exist" % ( key ))

def parse_cookies( filePath : str ):

    jar = req.cookies.RequestsCookieJar()
    
    with open( filePath , 'r' ) as cookie_file:
        for index,line in enumerate(cookie_file.readlines()):

            if line[0] == '#':
                continue

            sections = line.rstrip().split('\t')

            if len( sections ) != 7:
                if len( sections ) != 1: 
                    print( "Warn: line %d doesn't match cookie format with %d section" % ( index , len(sections )) )
                continue
            
            domain = sections[0]
            include_subdomain = sections[1]
            path = sections[2]
            secure = sections[3] == 'TRUE'
            expires = int(sections[4])
            name = sections[5]
            value = sections[6]

            jar.set( name , value )

    return jar 



ng_cookies = None

def ng_get( url ):
    global ng_cookies
    
    res = req.get( url, cookies = ng_cookies )

    if res.status_code == 404:
        raise Exception( "404#Page doesn't exist")
    if res.status_code == 302:
        raise Exception( "302#Doesn't have permission for this page. (age resitrct with invalid cookies ?)" )
    
    return res


def page_audio_parse( html : str ):
    soup = BeautifulSoup( html , 'html.parser')

    def find_embed_script( element ):
        return element.name == 'script' and 'var embed_controller' in element.text

    embed = soup.find(find_embed_script)


    # "url" : "<url>"
    url_start = embed.text.index( 'rl"' )
    url_end   = embed.text.index( '"' , url_start + 5 )

    url = embed.text[ url_start + 5:url_end ]

    # replace \/ with /
    url = url.replace("\\/", "/")

    # remove params
    url = url[:url.index('?')]
    

    return {
            "title" : soup.title.text,
            "url"   : url
            }

def page_audio_download( url : str, path : str ):
    
    audio_page = ng_get( url )
    audio = page_audio_parse( audio_page.text )

    filePath = path
    fileName = audio['title'] + '.mp3'
    
    if ( pathFilename := os.path.basename( filePath ) ) != '':
        fileName = pathFilename
        filePath = os.path.dirname( filePath )

    print( '[page_audio_download] url:', url )
    print( '[page_audio_download] path:', path )
    print( '[page_audio_download] fileName:', fileName )

    if os.path.exists( filePath ) == False:
        os.makedirs( filePath )

    outputPath = os.path.join( filePath , fileName ) 

    with open( outputPath , 'wb' ) as output:
        res = req.get( audio['url'], stream = True )
        content_length = int(res.headers['Content-Length'])

        print( '[page_audio_download] Content-Length:', content_length )
        
        chunk_size = 1024

        chunk_all   = math.ceil(content_length / chunk_size )
        chunk_index = 0
        file_size   = 0
        for chunk in res.iter_content( chunk_size = chunk_size ):
            print( '[%s] chunk %d/%d ' % (url,chunk_index,chunk_all) )
            output.write( chunk )
            chunk_index = chunk_index + 1
    
    audio["file"] = outputPath

    return audio

def page_user_audio_parse( html : str ):
    soup = BeautifulSoup( html , 'html.parser')

    submissions = soup.find_all( class_ = 'item-audiosubmission' )
    
    subs = {}

    for sub in submissions:
        href = sub.attrs['href']
        title = sub.attrs['title']

        subs[ title ] = href

    return subs

def page_user_audio_download( url : str , output : str ):
    res = ng_get( url )

    audios = page_user_audio_parse( res.text )

    for title , url in audios.items():
        page_audio_download( url , output)


def main():

    global ng_cookies

    output  = arg_str( '--output', './')

    cookiesPath = arg_str( '--cookies' ) 
    print( '[main] Load cookies with :' , cookiesPath )

    ng_cookies = parse_cookies( cookiesPath)
    print( '[main] Cookies loaded' , len(ng_cookies.keys()) )

    if len(__args__) == 0:
        raise Exception("ERROR: No URL")

    target_url = next( target for target in __args__ if not target.startswith('--'))
    print('[main] target_url', target_url )

    strip_url = target_url

    if '://' in strip_url:
        strip_url = strip_url[strip_url.index(':') + 3: ]

    is_audio_page = "newgrounds.com" in strip_url and "/audio/listen" in strip_url

    # hack somehting remove dot from www then check
    # because I don't know to to use virtual env and dont want to install package
    is_subs_page  = strip_url[:3] != 'www' and '.newgrounds.com' in strip_url

    if is_subs_page:
        if not '/audio' in target_url:
            if target_url[-1] != '/':
                target_url = target_url + '/'
            target_url = target_url + 'audio'
            print('[main] convert home page to submission url =>' , target_url )

    if is_subs_page:
        print('[main] user submission mode')
    elif is_audio_page:
        print('[main] audio file mode')
    else:
        raise Exception("Invalid URL")


    result = ''

    if is_subs_page:
        result = page_user_audio_download(
            target_url,
            output
        )
    elif is_audio_page:
        result = page_audio_download(
                target_url,
                output
        )

    print('Result')
    print( result )
    print('OK')
    pass

if __name__ == '__main__':
    main()
