
;
;;
;; jschmidt Thu Oct 15 11:02:12 EEST 2020 
;; example code to extract information rom spice
;;
;; index and description of spice routines:
;; https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/IDL/icy/index.html

;-----------------------------------------------------------------------------------
function Simple_BG_subtract,image,exclude_samples
;
; make a simple background subtraction:
; define background per line as the average brightness of the line
; exclude the region of the satellite from this background definition
; before definition of background shave off the brightess pixels (stars and gamma rays)
; 
; future improvement: fit a quadratic polynomial to the region outside the shadow of the satellite
; and away from the satellite itself, of the Enceladus plume (if any)
;

	nlines=n_elements(image(0,*))
	nsamples=n_elements(image(*,0))

	newimage=image
	for iline=0,nlines-1 do begin
	
		line=reform(image(*,iline))
		; excluding a range of samples from the definition of what background 
		; brightness is (for instance the satellite, or the Enceladus plume):
		cleanline=[line(0:exclude_samples(0)),line(exclude_samples(1):nsamples-1)]

		; set very bright pixels (stars and gamma rays) equal to the mean:
		mn=mean(cleanline)
		sigma=stddev(cleanline)
		ind=where(abs(cleanline-mn) gt 2d0*sigma,cnt)
		if cnt gt 0 then cleanline(ind)=mn
		; define the background brightness of this line
		bg=mean(cleanline)
		; subtract that from the line to define the new image
		newimage(*,iline)=image(*,iline)-bg

		if (0) then begin
		; debugging
			showline=237
			if iline eq showline then begin
			cleanindex=[indgen(exclude_samples(0)+1),indgen(nsamples-exclude_samples(1))+exclude_samples(1)]
			tek_color
			oplot,indgen(nsamples),replicate(showline,nsamples),col=2
			nwin
			plot,indgen(nsamples),line,thick=1
			oplot,cleanindex,cleanline,lin=2,col=2
			loadct,0,/silent
			stop
			endif
		endif

	endfor

return,newimage	
end

;-----------------------------------------------------------------------------------
pro SpiceExample

	def_plot
	tek_color

;	thick=1
;	!x.thick=thick
;	!y.thick=thick
;	!p.thick=thick

	loadct,0,/silent


;
; one example image
; 
	; load and plot the image
	imagedir='/Users/jschmidt/Projects/People/JoniL/ImageData/'
	image_id='N1533960372_1_CALIB.IMG'
	; NOTE: You can search in opus.pds-rings.seti.org
	; also directly for the product ID (under PDS Constraints)
	; if you then specifie N1533960372 as the search string
	; You will get this image as the only search result
	;
	; using read_vicar subroutine
	imgstruct=read_vicar(imagedir+image_id)
	; image time
	image_time_utc=imgstruct.lbl.image_mid_time
	; remove last character form image time string:
	len=strlen(image_time_utc)
	image_time_utc=strmid(image_time_utc,0,len-2)
	titlestring=imgstruct.lbl.target_name+', '+image_id+', '+image_time_utc
	img=imgstruct.img
	; hist_equal is histogram equalization (built in IDL)
	; which is usefull to see all details in the image
	; it will be good to replace this by sth of your own
	tvplot2,hist_equal(img),title=titlestring
	; display the range of samples that will be excluded from
	; the definition of background:
	exclude_samples=[450,650]
	oplot,[1,1]*exclude_samples(0),[0,1023],lin=2
	oplot,[1,1]*exclude_samples(1),[0,1023],lin=2

	; background subtracted image
	; shadow stands out better
	newimg=Simple_BG_subtract(img,exclude_samples)
	tvplot2,hist_equal(newimg),title=titlestring+', bg subracted'


;
; some geometry from spice
;

	; NOTE: also the metakernels (*.tm) loaded here must be
	; edited, so that they contain the correct path information on your disk
	; for the spicekernels they list
	; 
	; load general spice kernels (like information on leapseconds, rocks, frames)
	spicedir='/Users/jschmidt/arc/Spice/CassiniKernels/'
	commonkernel=spicedir+'mk/commons.tm'
	cspice_furnsh,commonkernel

	; load cassini and saturn-system specific spice kernels, for given year
	metakernel=spicedir+'mk/cas_2006_v26.tm'
	cspice_furnsh,metakernel

	; aberration correction not needed for this problem
	abcorr='NONE'

	; get spice ids for bodies we use
	cspice_bodn2c,'ENCELADUS',enceladus_id,found
	if not found then message,'ENCELADUS not found in spice kernel pool'
	cspice_bodn2c,'CASSINI',cassini_id,found
	cspice_bodn2c,'SATURN',saturn_id,found
	cspice_bodn2c,'SUN',sun_id,found

	; get the time as ephermeris time
	cspice_utc2et,image_time_utc,image_time_et

	; get a vector from Enceladus to Cassini. Note: This is in km!
	; (Note that SPKEZ would return also the velocity vector)
	CSPICE_SPKEZP,cassini_id,image_time_et,'J2000',abcorr,enceladus_id, $
				cassini_pos,lt_corr
	; vector from Enceladus to SUN
	CSPICE_SPKEZP,sun_id,image_time_et,'J2000',abcorr,enceladus_id, $
				sun_pos,lt_corr
	; phase angle
	costheta=total(cassini_pos*sun_pos)/CSPICE_VNORM(cassini_pos)/CSPICE_VNORM(sun_pos)
	theta=acos(costheta)*180d0/!dpi
	xyouts,/data,650,400,'PHASE ANGLE:'+string(theta)+' DEG'

	; vector from Enceladus to saturn
	CSPICE_SPKEZP,saturn_id,image_time_et,'J2000',abcorr,enceladus_id, $
				saturn_pos,lt_corr


	; some vectors in the frame of the camera
	instnm='cassini_iss_nac'
	; instrument id
	cspice_bodn2c,instnm,instid,found
	; number of the coordinate frame for the camera
	Room=10L
        cspice_getfov, instid, ROOM, shape, iframe, insite, bundry
	; J2nac: matrix to transform from J2000 to camera frame
	CSPICE_PXFORM,"J2000",iframe, image_time_et, J2nac
	; NOTE: Information on instrument frames in spice is given in
	; the instrument kernels (*.ik). For the ISS camera this is:
	; spicedir/ik/cas_iss_v10.ti
	; this is worth reading
	;
	; get the sun vector in the frame of the NAC 
	cspice_mxv,J2nac,sun_pos,nacsun
	esun =[nacsun (0),nacsun (1)]
        esun=-esun/sqrt(esun(0)*esun(0)+esun(1)*esun(1))*100
	; plot the sun vector somewhere
	tek_color
	arrow,700,700,700+esun(0),700+esun(1),col=7,/data,thick=3
	xyouts,/data,810,750,'SUN',col=7
	; get the vector to saturn in the frame of the NAC 
	cspice_mxv,J2nac,saturn_pos,nacsat
	esat =[nacsat (0),nacsat (1)]
        esat=-esat/sqrt(esat(0)*esat(0)+esat(1)*esat(1))*100
	; plot the saturn vector
	arrow,700,700,700+esat(0),700+esat(1),col=7,/data,thick=3
	xyouts,/data,810,650,'SATURN',col=7

;
; unload spice kernels
;
	cspice_unload,commonkernel
	cspice_unload,metakernel

end
