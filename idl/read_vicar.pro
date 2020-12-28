;;# /* Time-stamp: <2006-09-08 17:45:45 msremac> Format is yy/mm/dd hh:mm:ss */
;; $Id: read_vicar.pro,v 1.1.1.1 2013/08/29 08:35:10 cvsuser Exp $
;;
;;
;; VICAR file format
;;
;; http://www-mipl.jpl.nasa.gov/vicar/vic_file_fmt.html
;; http://www.fileformat.info/format/vicar2/
;;
;; ========================================================================
;; ========================================================================
;; ========================================================================
FUNCTION read_vicar_label,instr,l_tags
  str = instr
  res = -1

  strwht  = ' '+string(9b)+string(10b)+string(13b) ; all white characters
  strm00  = '^['+strwht+']+'
  strm01  = '^[_A-Z0-9]+'
  strm02  = '^['+strwht+']*=['+strwht+']*'
  strm03  = '^\([^\(\)]*\)'
  strm04  = "^'[^']*'"
  strm05  = '^[^'+strwht+']+'
  strm06  = '^['+strwht+']*(\-?|\+?)[0-9]+['+strwht+']*$'

  ;; default tags
  lbl     = { $
            LBLSIZE: 0L, $
            TYPE: 'IMAGE', $
            DIM:  3L, $
            EOL:  0L, $
            ORG:  'BSQ',  $
            N1: -1L, $
            N2: -1L, $
            N3: -1L, $
            N4:  0L, $
            NBB: 0L, $
            NLB: 0L, $
            HOST: 'VAX-VMS', $
            INTFMT: 'LOW', $
            REALFMT: 'VAX' $
            
            }
  l_tags  = TAG_NAMES(lbl)

  while( strlen(str) gt 0 AND strmid(str,0,1) ne string(0b) ) do begin
     flag = 0b
     
     if( STREGEX(str,strm00,length=len) ge 0 ) then begin
        str = STRMID( str, len ) ; chop whites
     endif

     tag = ''
     if( STREGEX(str,strm01,length=len) ge 0 ) then begin
        tag = strmid( str, 0, len )
        str = STRMID( str, len ) ; rest
     endif
     
     if( STREGEX(str,strm02,length=len) ge 0 ) then begin
        str = STRMID( str, len ) ; chop [whites]*=[whites]*
     endif else begin
        str = ''                ; there should be =!
     endelse
     
     val  = ''
     frd  = 1b
     ;; frst = strmid( str , 0 , 1 ) ; 1st character

     if( frd AND STREGEX(str,strm03,length=len) ge 0 ) then begin
        val = strmid( str, 1, len - 2 )
        val = STRSPLIT( val , ',' , /extract )
        str = STRMID( str, len ) ; rest
        frd = 0b

        val  = strtrim( val , 2 )
        tmp1 = strmid( val , 0 , 1 ) eq "'"
        tmp2 = strmid( val , 0 , 1 , /reverse ) eq "'"
        if( MIN(tmp1) eq 1 AND MIN(tmp2) eq 1 ) then begin
           for i=0,N_ELEMENTS(val)-1 do begin
              val[i] = strmid(val[i],1,STRLEN(val[i])-2)
           endfor
        endif

        tmp = STREGEX(val,strm06,/boolean)
        if( MIN(tmp) eq 1 ) then begin
           val = LONG( val )
        endif
     endif
     
     if( frd AND STREGEX(str,strm04,length=len) ge 0 ) then begin
        val = strmid( str, 1, len - 2 )
        str = STRMID( str, len ) ; rest
        frd = 0b
     endif
     
     if( frd AND STREGEX(str,strm05,length=len) ge 0 ) then begin
        val = strmid( str, 0, len )
        str = STRMID( str, len ) ; rest
        frd = 0b
     endif
     
     if( N_ELEMENTS(val) eq 1 ) then begin
        tmp = STREGEX(val,strm06,/boolean)
        if( tmp[0L] ) then val = LONG(val)
     endif

     if( tag ne '' ) then begin
        ;; print,'>>'+tag+'<< ===>>',val
        l_tags = TAG_NAMES(lbl)
        ind    = where( tag eq l_tags , cnt )
        if( cnt eq 0 ) then begin
           lbl = CREATE_STRUCT( tag , val , lbl )
        endif else begin
           lbl.(ind[0L]) = val
        endelse
     endif

     if( tag eq '' ) then str = '' ; smth bad, there was no tag!
  endwhile

  ;; organization of the file
  lbl.ORG = STRUPCASE(strtrim(lbl.ORG,2))
  if( lbl.ORG eq 'BSQ' ) then begin
     lbl.N1 = lbl.NS
     lbl.N2 = lbl.NL
     lbl.N3 = lbl.NB
  endif
  if( lbl.ORG eq 'BIL' ) then begin
     lbl.N1 = lbl.NS
     lbl.N3 = lbl.NL
     lbl.N2 = lbl.NB
  endif
  if( lbl.ORG eq 'BIP' ) then begin
     lbl.N2 = lbl.NS
     lbl.N3 = lbl.NL
     lbl.N1 = lbl.NB
  endif

  l_tags = TAG_NAMES(lbl)
  ;;  if( N_ELEMENTS(lbl) eq 0 ) then lbl = -1
  ;; help,lbl,/st
  RETURN,lbl
END
;; ========================================================================
;; ========================================================================
;; ========================================================================
FUNCTION read_vicar,filename,silent=silent,noeol=noeol
res = -1

if( N_ELEMENTS(silent) eq 0 ) then print,'Reading: '+filename
openr,unitt,filename,/GET_LUN

;; ---------- READ LABEL --------------
;; read all initial spaces and LBLSIZE keyword!
rd_size = 16                    ; minimum number of bytes to read
lbl_00  = READ_BINARY(unitt, DATA_TYPE=1, DATA_DIMS=[rd_size])
lbl_rd  = N_ELEMENTS( lbl_00 )
str_00  = STRING( lbl_00 )
flag_rd = 1b
flag_ok = 0b

strwht  = ' '+string(9b)+string(10b)+string(13b) ; all white characters
strm00  = '^['+strwht+']+'
strm01  = '^LBLSIZE['+strwht+']*=['+strwht+']*[1-9][0-9]+['+strwht+']+'

;; find first label: LBLSIZE
while( flag_rd AND (not EOF(UNITT)) ) DO BEGIN
   tmp     = READ_BINARY(unitt, DATA_TYPE=1, DATA_DIMS=[rd_size])
   lbl_00  = [ lbl_00 , tmp ]
   lbl_rd = lbl_rd+N_ELEMENTS(tmp)
   str_00  = str_00  + STRING(tmp)
   
   if( STREGEX(str_00,strm00,length=len) ge 0 ) then begin
      str_00 = STRMID( str_00, len ) ; chop whites
   endif

   len = STRLEN( str_00 )
   if( len ge 7 AND STRMID(str_00,0,7) ne 'LBLSIZE' ) then begin
      message,'LBLSIZE is not the first label in file: '+filename
   endif

   if( STREGEX(str_00,strm01,/BOOLEAN) ) then begin
      ;; help,str_00
      tmp     = strsplit( str_00, '=' , /extract )
      LBLSIZE = LONG( tmp[1] )
      flag_rd = 0b
      flag_ok = 1b
   endif

   ;; label can not be larger than 1MB
   if( lbl_rd gt 1048576L ) then flag_rd = 0b
endwhile

if( NOT(flag_ok) ) then begin
   message,'Not found LBLSIZE in file: '+filename
endif

;; rest of the label!
tmp    = READ_BINARY(unitt, DATA_TYPE=1, DATA_DIMS=[LBLSIZE-lbl_rd] )
lbl_00 = [ lbl_00 , tmp ]
str_00 = str_00 + STRING( tmp )
;;print,str_00


lbl = read_vicar_label( str_00 , list_tags )
;;help,lbl,/st
;;help,LBLSIZE,lbl_00, list_tags
;; ------------------------------------

;; --- read binary header (if present) -----
binary_header = -1
if( lbl.NLB gt 0 ) then begin
   tmp = READ_BINARY(unitt, DATA_TYPE=1, DATA_DIMS=[lbl.RECSIZE,lbl.NLB] )
   binary_header = REFORM( tmp , lbl.RECSIZE,lbl.NLB )
endif

;; --- pixel type? ----
pix_siz = -1                    ; pixel size in bytes
is_int  = -1                    ; is it integer (1) or not(0)
is_comp = 0b                    ; is it complex (1) or not(0)
if( lbl.FORMAT eq 'BYTE' ) then begin
   pix_siz = 1
   is_int  = 1b
endif
if( lbl.FORMAT eq 'HALF' OR lbl.FORMAT eq 'WORD'  ) then begin
   pix_siz = 2
   is_int  = 1b
endif
if( lbl.FORMAT eq 'FULL' OR lbl.FORMAT eq 'LONG'  ) then begin
   pix_siz = 4
   is_int  = 1b
endif
if( lbl.FORMAT eq 'REAL' ) then begin
   pix_siz = 4
   is_int  = 0b
endif
if( lbl.FORMAT eq 'DOUB' ) then begin
   pix_siz = 8
   is_int  = 0b
endif
if( lbl.FORMAT eq 'COMP' OR lbl.FORMAT eq 'COMPLEX'  ) then begin
   pix_siz = 8
   is_int  = 0b
   is_comp = 1b
endif

if( pix_siz lt 1 OR is_int lt 0 ) then begin
   message,'Unrecognized FORMAT, here='+string(lbl.FORMAT)
endif

tmp = (lbl.RECSIZE-lbl.NBB)/double(lbl.N1)
if( pix_siz NE LONG(tmp+0.5) ) then begin
   message,'Size of pixels does not match RECSIZE!'
endif

tmp = lbl.REALFMT ne 'IEEE' AND lbl.REALFMT ne 'RIEEE'
if( NOT(is_int) AND tmp ) then begin
   message,'Uknown real type: '+string(lbl.REALFMT)
endif

if( LBL.N4 gt 0 ) then begin
   message,'There is fourth dimension! Do not know how to read it.'
endif

if( is_int ) then begin
   if( pix_siz eq 1 ) then pix_type = 1
   if( pix_siz eq 2 ) then pix_type = 2
   if( pix_siz eq 4 ) then pix_type = 3
   nname = ['BYTE','INT','LONG']
   nind  = pix_type - 1
   nmsg  = nname[nind] + ' ('+strtrim(pix_siz,2)+'bytes)'
endif else begin
   if( is_comp ) then begin
      pix_type = 6
      nmsg     = 'COMPLEX (8bytes)'
   endif else begin
      if( pix_siz eq 4 ) then pix_type = 4
      if( pix_siz eq 8 ) then pix_type = 5
      nname = ['FLOAT','DOUBLE']
      nind  = pix_type - 4
      nmsg  = nname[nind] + ' ('+strtrim(pix_siz,2)+'bytes)'
   endelse
endelse

;; --- read image ------
img = -1
bin_prefix = -1
if( lbl.NBB gt 0 ) then begin
   bin_prefix = BYTARR(lbl.nbb,lbl.n2,lbl.n3)
   bin_prefix = REFORM( bin_prefix, lbl.nbb,lbl.n2,lbl.n3)
endif
img = MAKE_ARRAY( lbl.n1, lbl.n2, lbl.n3 , TYPE=pix_type )
img = REFORM( img, lbl.n1, lbl.n2, lbl.n3 )

if( N_ELEMENTS(silent) eq 0 ) then begin
   print,'   Image: '+nmsg+'  '+$
         strtrim(lbl.n1,2)+'x'+strtrim(lbl.n2,2)+'x'+strtrim(lbl.n3,2)
endif

if( lbl.NBB gt 0 ) then begin
   ;; slower way, there is also binary prefix of lbl.NBB bytes
   for i3=0L,lbl.n3-1 do begin
      for i2=0L,lbl.n2-1 do begin
         bin_prefix[*,i2,i3] = READ_BINARY(unitt,DATA_TYPE=1,DATA_DIMS=[lbl.NBB] )
         img[*,i2,i3] = READ_BINARY(unitt,DATA_TYPE=pix_type,DATA_DIMS=[lbl.N1] )
      endfor 
   endfor 
endif else begin
   img = READ_BINARY(unitt,DATA_TYPE=pix_type,DATA_DIMS=[lbl.N1,lbl.N2,lbl.N3] )
endelse

;; ---------- what is our indianess? -----------
me_endian = 1
SWAP_ENDIAN_INPLACE,me_endian,/SWAP_IF_BIG_ENDIAN
endian_me   = me_endian ne 1    ; false(0)=small, true(1)=big

if( is_int ) then begin
   endian_file = lbl.INTFMT eq 'HIGH'
endif else begin
   endian_file = lbl.REALFMT eq 'IEEE'
endelse

if( pix_siz gt 1 AND (endian_me XOR endian_file) ) then begin
   SWAP_ENDIAN_INPLACE, img
endif

;; ---- read EOL label (if present) -----
eol = -1
IF( (not EOF(UNITT)) AND N_ELEMENTS(noeol) eq 0 AND lbl.eol ) then begin
   eol = READ_BINARY(unitt,DATA_TYPE=1)
endif

FREE_LUN,unitt

res = { $
      filename: filename, $
      lbl:      lbl, $
      n1:       lbl.n1, $
      n2:       lbl.n2, $
      n3:       lbl.n3, $
      bin_header: binary_header, $
      bin_prefix: bin_prefix, $
      img:      REFORM(img), $  ; put 3d into 2d if one if DIMs is 1
      eol:      eol  $
      }

if( N_ELEMENTS(silent) eq 0 ) then help,res,/st
RETURN,res
END
;; ========================================================================
;; ========================================================================
;; ========================================================================
