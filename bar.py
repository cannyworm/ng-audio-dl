import math
import time
import sys
import shutil
import random


def csi( a : str , n : str | int ):
    return "\033[" + str(n) + a

def cursor_back( n : int ):
    return csi( 'D' , n )

def esc( a ):
    # return "ESC" + a
    return csi( 'm' , a )

DEFAULT_BAR_WIDTH = math.floor(shutil.get_terminal_size()[0] / 3)

class Bar():
    title    = "[undefined]"    
    progress_length = 0
    progress = 0

    bar_width = 0
    
    bar_styles = [
        "▰▱",
        "▰═"
    ]
    
    finish = '✅'

    spiner_styles = [
        "|/-\\",
        "◴ ◷ ◶ ◵",
        "⠁⠂⠄⡀⢀⠠⠐⠈",
        # "▁ ▂ ▃ ▄ ▅ ▆ ▇ █ ▇ ▆ ▅ ▄ ▃ ▁"
    ]

    bar_style_index = 0
    spiner_style_index = random.randint( 0 , len( spiner_styles ) - 1 )
    
    spiner_style = spiner_styles[ spiner_style_index ]
    bar_fill = bar_styles[bar_style_index][0]
    bar_void = bar_styles[bar_style_index][1]

    init = False

    def __init__(self, title : str , length : int , bar_width : int = DEFAULT_BAR_WIDTH) -> None:
        self.title = title
        self.progress_length = length
        self.bar_width = bar_width
        self.finish = self.color( "$92$01" + self.finish + "$00")

    def add( self , value : int ):
        self.progress += value
    
    def color( self , content : str ) -> str:
        text = ""

        escapes = content.split('$')
        for escape in escapes:
            if len(escape) == 0 or not escape[0].isnumeric():
                text += escape
                continue

            e = escape[:2] 
            if e[0] == '0':
                e = e[1]

            text += esc( e ) + escape[2:]

        return text
    
    def render_title( self ) :
        return self.color( "$01[$00%s$01]$00" ) % self.title
    
    def progress_ratio( self ):
        return self.progress / self.progress_length 

    def bar_fill_width( self ):
        return math.floor( self.progress / self.progress_length * self.bar_width )

    def render_spiner( self ) :
        if self.is_finish():
            return self.finish

        return self.spiner_style[ math.floor( self.progress_ratio() * 100 ) % len( self.spiner_style ) ]

    def render_bar( self ):
        bar = self.color( "> ( " + self.render_spiner() + " ) ")
        # ▰ ═
        # ▰ ▱
    
        # render filled path
        for i in range( self.bar_fill_width() ):
            color = "$"

            r = i / self.bar_width
            if r > 0.75:
                color += '34'
            elif r > 0.50:
                color += '35'
            elif r > 0.25:
                color += '35'
            else:
                color += '95'


            bar += self.color( color + self.bar_fill + "$00"  )
        
        bar += self.color("$00")

        # render unfilled
        for i in range( self.bar_width - self.bar_fill_width() ):
            bar += self.color( self.bar_void  )

        bar += ""

        return bar
    
    def is_finish( self ):
        return self.progress_length == self.progress

    def render_progress( self ):
        return "%03d/%03d (%.2f%%)" % ( self.progress , self.progress_length , self.progress_ratio() * 100 )
    
    init_static = False

    def render( self ):

        if not self.init_static:
            self.init_static = True
            print( self.render_title() )

        bar = self.render_bar() + " "
        progress = self.render_progress()

        bar_start = len( bar ) + len( progress )
        end = cursor_back( bar_start )

        print( bar +  progress + end , end = '' )

        if self.is_finish():
            print()
        else:
            sys.stdout.flush()
    
    pass
