/**
  author:       L. Sauer 2011 (c); lsauer.com
  project:      KeyBoarder
  description:  keyBoarder is a small, fast javascript library for dynamically rendering visually appealing, navigatable keyboard shortcuts.
  license:      MIT license (commercial use is ok)
*/
/*--------------START OF CONFIG--------------*/
//kbparams {object}: configuration parameters to be passed to the keyboarder constructor; usually the css-classNames of the Elements to be rendered suffices
//it's okay to pass no parameters and use the default ones: e.g. kb = new KeyBoarder()

kbparams = {
	clsNames : ["content"],				//css-classNames of the Elements in which shortcuts should be rendered e.g. <div class="content"> My blog-post content </div>
										//mixed-type: string of one class or array of classnames
	isDebug : false,					//useful during development; provides verbose output
	safeMode : false,					//fallback to an older better tested Regular expression
	concatenator : '+',					//the concat symbol used for declaring shortcuts e.g. ALT + X
	matchAtLeast : 0, 					//number of consecutive keys present for a match to occur
	keyHtmlElem : 'kbd',				//the HTML element type in which shortcuts are embedded 
	isStartCasing : true,				//if your shortcuts start with an upper case like this Alt + Ctrl + X
	isBothCasing : true,				//explicitly allows StartCasing and UPPERCASING
	stripPunctuation : true,			//whether any matched ASCI print symbols e.g. *#%&... should remain with the key or be stripped

	/**
	 * The most common keycodes defined by :
	 * @type {Object.<number>}
	 * @const
	 */
	KEYMAP : {
		/*delete: just for demonstration*/
		UPPERCASE : 0,
		Startcase : 0,
		
		STRG: 16,
		CTRL: 17,
		/*CTRL: 17,
		ALTRIGHT : 17,*/
		CTRLRIGHT: 18,
		CTRLR: 18,
		SHIFT: 16,
		RETURN: 13,
		ENTER: 13,
		BACKSPACE: 8,
		BCKSP:8,
		ALT: 18,
		SPACE: 32,
		TAB : 9,
		WIN: 91,
		INSERT: 0,
		END :0,
		PAGE : 0,
		HOME :0,
		MAC: 91,
		FN: null,
		UP: 38,
		DOWN: 40,
		LEFT: 37,
		RIGHT: 39,
		ESC: 27,
		DEL: 46,
		F1: 112,
		F2: 113,
		F3: 114,
		F4: 115,
		F5: 116,
		F6: 117,
		F7: 118,
		F8: 119,
		F9: 120,
		F10: 121,
		F11: 122,
		F12: 123,
		PUNCTALNUM : 36 //sets the start for recognizing alphanummerical and punctuations
	},
}

/*--------------END OF CONFIG--------------*/
/**
HTMLElement css-class setter/getter Object
HTML Elements can have several classes, separated by space ' '. The rightmost css-class takes precedence
author: L.Sauer 2011, MIT License
*/
isOpera = (/opera/i.test(navigator.userAgent)) ? true : false;

Classy = function(el){
	//constructor
	if(el && el.constructor === String ){
		el = document.getElementsByClassName(el)[0];
	}
	//private shared
	var	that = el; //set to DOM element
	return {
		self : el,
		//set a new element
		set : function(ele){if(!ele.length){ this.self = ele; }else{this.self = ele[0]; that = ele;} return this;}, 
		//object, function, callbackEnd
		foreach : function (cls, o, f) {	//classname, object, function
			for(var i=0; i<o.length; i++) { // iterate through all objects
				f(cls, o[i]); // execute a function and make the obj, objIndex available
			}
		},
		has : function (cls, ele) {
			//this.foreach(this.self, has, )
			if( this.self ) {ele =  this.self;}
				var reg = new RegExp('(^|\\s)' + cls + '(\\s?)');
				return ele.className.match(reg);
		},
		add : function (cls, ele) {
			if( this.self ) {ele =  this.self;}
			if (!this.has(cls, ele)) {ele.className += ' ' + cls;}
			return this;
		},
		del : function (cls, ele) {
			if( this.self ) {ele =  this.self;}
			if (this.has(cls, ele)) {
				var reg = new RegExp('(^|\\s)' + cls + '(\\s?)');
				ele.className = ele.className.replace(reg, ' ');
			}
			return this;
		},
		repl : function (cls,clsNew, ele)  {
			if( this.self ) {ele =  this.self;}
			if(this.has(cls, ele)) {
				this.del(cls, ele);
			}
			this.add(clsNew, ele);
			return this;
		},
		focus : function(ele){
			if( this.self ) {ele =  this.self;}
			var i = 100;var pos = {x:0,y:0};
			while(ele != null ){
				pos.x += ele.offsetLeft;
				pos.y += ele.offsetTop;
				ele = ele.offsetParent;
			  }
			window.scrollTo(pos.x,pos.y);
		},
		prototype : {toString :function(){
			return JSON.stringify(self)
		}},
	};
};

with ((window && window.console && window.console._commandLineAPI) || {}) {

/**
 keyBorder: Create interactive shorcut keys from text
 
 @constructor
 @param clsNames {Object.<string>| Object.<object>}
 	class-name of the html elements which KeyBoarder should process/parse
 For a complete list of options, see the CONFIG object in the keyBoarder 'class'
 */
var KeyBoarder = (function () {
	//outer function expressions is used to return an class-like object

	//'private static variables'
	//reference for css class-setter/getter
	var csscls =  new Classy();
	
	/** 
	Default parameters
	 @type {Object.<string>}
	 @const
	 */
	var KEYCODESBASIC = {
		'backspace' : '8',
		'tab' : '9',
		'enter' : '13',
		'shift' : '16',
		'ctrl' : '17',
		'alt' : '18',
		'pause_break' : '19',
		'caps_lock' : '20',
		'escape' : '27',
		'page_up' : '33',
		'page down' : '34',
		'end' : '35',
		'home' : '36',
		'left_arrow' : '37',
		'up_arrow' : '38',
		'right_arrow' : '39',
		'down_arrow' : '40',
		'insert' : '45',
		'delete' : '46',
		'0' : '48',
		'1' : '49',
		'2' : '50',
		'3' : '51',
		'4' : '52',
		'5' : '53',
		'6' : '54',
		'7' : '55',
		'8' : '56',
		'9' : '57',
		'a' : '65',
		'b' : '66',
		'c' : '67',
		'd' : '68',
		'e' : '69',
		'f' : '70',
		'g' : '71',
		'h' : '72',
		'i' : '73',
		'j' : '74',
		'k' : '75',
		'l' : '76',
		'm' : '77',
		'n' : '78',
		'o' : '79',
		'p' : '80',
		'q' : '81',
		'r' : '82',
		's' : '83',
		't' : '84',
		'u' : '85',
		'v' : '86',
		'w' : '87',
		'x' : '88',
		'y' : '89',
		'z' : '90',
		'left_window key' : '91',
		'right_window key' : '92',
		'select_key' : '93',
		'numpad 0' : '96',
		'numpad 1' : '97',
		'numpad 2' : '98',
		'numpad 3' : '99',
		'numpad 4' : '100',
		'numpad 5' : '101',
		'numpad 6' : '102',
		'numpad 7' : '103',
		'numpad 8' : '104',
		'numpad 9' : '105',
		'multiply' : '106',
		'add' : '107',
		'subtract' : '109',
		'decimal point' : '110',
		'divide' : '111',
		'f1' : '112',
		'f2' : '113',
		'f3' : '114',
		'f4' : '115',
		'f5' : '116',
		'f6' : '117',
		'f7' : '118',
		'f8' : '119',
		'f9' : '120',
		'f10' : '121',
		'f11' : '122',
		'f12' : '123',
		'num_lock' : '144',
		'scroll_lock' : '145',
		'semi_colon' : '186',
		'equal_sign' : '187',
		'comma' : '188',
		'dash' : '189',
		'period' : '190',
		'forward_slash' : '191',
		'grave_accent' : '192',
		'open_bracket' : '219',
		'backslash' : '220',
		'closebracket' : '221',
		'single_quote' : '222'
	}
	
	//default parameters
	var CONFIG = {		
	clsNames : ["content", "claro"],	//css-classNames of the Elements in which shortcuts should be rendered e.g. <div class="content"> My blog-post content </div>
										//mixed-type: string of one class or array of classnames
	isDebug : false,					//useful during development; provides verbose output
	safeMode : false,					//fallback to an older better tested Regular expression
	concatenator : '+',					//the concat symbol used for declaring shortcuts e.g. ALT + X
	matchAtLeast : 0, 					//number of consecutive keys present for a match to occur
	keyHtmlElem : 'kbd',				//the HTML element type in which shortcuts are embedded 
	isStartCasing : true,				//if your shortcuts start with an upper case like this Alt + Ctrl + X
	isBothCasing : true,				//explicitly allows StartCasing and UPPERCASING
	stripPunctuation : true,			//whether any matched ASCI print symbols e.g. *#%&... should remain with the key or be stripped
		/**
		 * The most common keycodes defined by :
		 * @type {Object.<number>}
		 * @const
		 */
		KEYMAP : {
			STRG: 17,
			/*CTRL: 17,*/
			CTRLRIGHT: 18,
			CTRLR: 18,
			SHIFT: 16,
			RETURN: 13,
			ENTER: 13,
			BACKSPACE: 8,
			BCKSP:8,
			ALT: 18,
			ALTRIGHT: 17,
			SPACE: 32,
			WIN: 91,
			MAC: 91,
			FN: null,
			UP: 38,
			DOWN: 40,
			LEFT: 37,
			RIGHT: 39,
			ESC: 27,
			DEL: 46,
			F1: 112,
			F2: 113,
			F3: 114,
			F4: 115,
			F5: 116,
			F6: 117,
			F7: 118,
			F8: 119,
			F9: 120,
			F10: 121,
			F11: 122,
			F12: 123
		},
	};
	//internal variables / 'constants'
	var VERSION = 0.6;
	var DATE = '20/08/2011';
	var NAME = 'initial release';
	var kbkeys = []; 		//array with kb keys: serves as check wether an key is in the array; for generation the regex; 
	var KEYMAPIDX = {}		//holds a count of a highlighted key, when navigating kbd elements by pressing the corresponding key
	var KEYMAPflip = {} 	//flipped keymap to get the literal key from a keycode
	var Startcasing = function(str){ 
		if(!CONFIG.isStartCasing) return str; else return str.toUpperCase()[0] + str.substr(1,str.length).toLowerCase();
	}
	
	// global static
	isKeyBoarder = true;
	
	var __info__ = function () {
		return [NAME, ': <', VERSION, '>'].join('');
	};
	
	/**
	 keyBorder: Create interactive shorcut keys from text
	 
	 @constructor
	 @param kbconfig {Object.<object>}
		object with configuration options
	 For a complete list of options, see the CONFIG object in the keyBoarder 'class'
	 */
	var clsKb =  function (kbconfig) {
		//set self reference for public static methods
		this.self = this;
		if(arguments.length === 0){
			var kbconfig = {};
		}
		
		//override default settings
		for(var i in kbconfig){
			CONFIG[i] = kbconfig[i];
		}
		
		//build array with kbkeys, and index
		for(var i in CONFIG.KEYMAP){
			kbkeys.push( Startcasing(i) );
			if(CONFIG.isBothCasing)
				kbkeys.push( i.toUpperCase() );
			//KEYMAPIDX[i] = 0;
			//KEYMAPflip[ CONFIG.KEYMAP[i] ] = i; //+= i+'|'...to handle one to many relationships
		}
		//add basic keymap to the prototype chain
		CONFIG.KEYMAP.__proto__ = KEYCODESBASIC;
		for(var i in CONFIG.KEYMAP){
			KEYMAPIDX[i.toLowerCase()] = 0;
			KEYMAPflip[ CONFIG.KEYMAP[i] ] = i; //+= i+'|'...to handle one keyCode to many keyLiterals - relationships
		}
		//private variables
		
		//attach event handlers for shortcut navigation
		var elbody = document.getElementsByTagName('body')[0];
		elbody.addEventListener( 'keydown', KeyBoarder.highlightKeys);
		elbody.addEventListener( 'keyup', KeyBoarder.highlightKeys);
		
		var regkeys = kbkeys.join('|');
		if( !CONFIG.safeMode ){
			var qsym = CONFIG.matchAtLeast ? '+' : '?'; // if consecutive keys are set, then at least one concatenator symbol must exist
			var regstr = new RegExp('[\\s|,\\-]?((?:'+regkeys+'|F\\d\\d?\\s)\\s*\\'+CONFIG.concatenator+qsym+
							'\\s*){1,4}([A-Z0-9\\*\\+\\-](\\s*\\+\\s*[A-Z0-9])?|[A-Z0-9]\\'+CONFIG.concatenator+'[A-Z0-9]?){0,1}(?:[,\\s\\"\\\'<\\/])','g');
		}else{
			var regstr = /[\s|,]?((?:STRG|CTRL|SHIFT|RETURN|ENTER|ALT|ALTR|SPACE|WIN|FN|UP|DOWN|LEFT|RIGHT|ESC|DEL)\s{0,2}\+\s?){1,2}[A-Z0-9][,]?\s/g
		}
		if( CONFIG.isDEBUG )
			console.log(regstr)
		var regs = new Array(
			//first match function keys
			// /[\s|,-]?((?:STRG|CTRL|SHIFT|RETURN|ENTER|ALT|ALTR|SPACE|WIN|FN|UP|DOWN|LEFT|RIGHT|ESC|DEL|F\d\d?\s)\s*\+?\s*){1,4}([A-Z0-9]|[A-Z0-9]\+[A-Z0-9]?){0,1}[,]?\s/g,
			//this will also match RETURNR, WING etc.., since JS regex has no lookbehind. We can conveniently filter these later
			regstr
			//second, match single keys, etc...; useful for complex consecutive regex operations
			// /[\s|,-](STRG|CTRL|SHIFT|RETURN|ENTER|ALT|ALTR|SPACE|WIN|FN|UP|DOWN|LEFT|RIGHT|ESC|DEL)[\s|,]/g
		);
		/*
		//dynamically build a regex from KEYMAP
		var regstr = '[\\\\s|,\\\\-\\\\'+CONFIG.concatenator+']?((?:'
		var regsep = '[\\\\\s\\\\'+CONFIG.concatenator+'\\\\-~]*|'
		for(var i in CONFIG.KEYMAP){
			regstr += StartCase(i) +'|'//+ regsep
		}
		regstr += '){0,3}\\\\'+CONFIG.concatenator+'\\\\s?){1,2}[A-Z0-9][,]?\\\\s'
		regs[0] = new RegExp(regstr);
		console.log(regstr);
		this.regs = regs;
		*/
		
		/**
			function regmatch is passed the Regex-match from String.replace and embedds the match in html tags
			@param m {Object.<string>} ...contains entire match
		*/	
		var regmatch = function(m){
			if( CONFIG['isDebug'] ){
				console.log("matches:", m);
			}
			//filter, required because the regexp will also match any KEY\s*\+?\s*[:alnum:] e.g. WING, WINR, WIN  T courtesy of a JS regex's lack of lookbehind
			if( m.indexOf( CONFIG.concatenator ) === -1 && kbkeys.indexOf(m.trim()) === -1 ) //single key, yet not defined, so a mismatch
				return m;
			var tmp;
			if( CONFIG.matchAtLeast && (tmp = m.match(RegExp('\\'+CONFIG.concatenator, 'g') )) !== null && tmp.length < CONFIG.matchAtLeast)
				return m;
			//to a type cast, actually that would be: String(m)
			m = m.toString();
			//further clean up of the passed string
			if( CONFIG.stripPunctuation )
				m = m.replace( RegExp(',|\\"|\\-|\\\'|\\*|\\#|\\\\|\\;|\\:|\\||\\.|\\!|\\$|\\&|\\%', 'g'), '');
			
			var arg, endtag = ''; concat = '<b class="kbConcat">'+ CONFIG.concatenator +'</b>';
			if( m[m.length-1] === '<' ){//dirty fix; captured part of the endtag
				m = m.substr(0,m.length-1);
				endtag =  '<';
			}	
			var elHtml = CONFIG.keyHtmlElem;
			//'concatenator' must not be the first character e.g. text .... shortcut is +ALT text continues...
			if( m.indexOf( CONFIG.concatenator ) > -1 ){
				arg = m.split( RegExp('\\s*\\'+CONFIG.concatenator+'\\s*') );
				//faster than forEach / for in
				for(var i=0; i<arg.length; i++){
					//all individual CSS-Key classes are of the form .kbKEY {...} e.g. .kbCTRL {....}, 
					arg[i] = '<'+ elHtml +' class="kbKey kb'+ arg[i].toString().toUpperCase().trim() +'">' + arg[i].toString().trim() + '</'+ elHtml +'>'; 
				}
				arg = arg.join( concat );
			} else { // simple key e.g. ' ESC '
				arg = '<'+ elHtml +' class="kbKey kb'+m.toUpperCase().trim()+'">' + m.trim() + '</'+ elHtml +'>'; 
			}
			//commas before and after are allowed and included in the total-match
			return arg.replace(/,|\-/g, '')+endtag;
		}
		//add as a method to this class
		this.regmatch = regmatch;
		//string: HTML Elements property holding the html content
		this.htmlproptext = ''
		
		var restore = function(){
			for(var i=0; i< CONFIG.clsNames.length; i++) {
				var els = document.getElementsByClassName( CONFIG.clsNames[i] )[0];
				for(var j=0; j< els.length; j++)
				{				
					var ij_indexOrigtext = CONFIG.clsNames[i]+','+j; 
					if(typeof el === 'undefined')
						continue;
					if( typeof self.originaltext[ ij_indexOrigtext ] !== 'undefined'){
						el[self.htmlproptext] = self.originaltext[ ij_indexOrigtext ];
						return true;
					}else{
						return false;
					}
				}
			}
		}
		this.restore = restore;
		
		//Intitiliazing and update, e.g. when changing the classNames
		var init = function(){
			if(arguments.length > 0){ //were configuration parameters passed?
				if( kbconfig.constructor === String ){
					CONFIG.clsNames.push(kbconfig); //add
				} else if( kbconfig.constructor === Object ){
					CONFIG.clsNames = kbconfig['clsNames']; //replace
				}else{
					throw new TypeError("unexpected Object passed to constructor");	
				}
			}
			var reFlag = 'g';	//not used; global flag; RegExp's second param; 
			//var el, text, reFlag, regs;
			for(var i=0; i< CONFIG.clsNames.length; i++)
			{
				//variables declared in the immediate var-scope aid the garbage collector in being able to collect sooner dead references
				var els = document.getElementsByClassName( CONFIG.clsNames[i] );
				for(var j=0; j< els.length; j++)
				{
					var el = els[j];
					if(typeof el === 'undefined')
						continue;
					if( typeof this.originaltext === 'undefined'){
						//contains the original, unaltered html
						this.originaltext = {};
					}
					var ij_indexOrigtext = CONFIG.clsNames[i]+','+j; 
					if( typeof this.originaltext[ ij_indexOrigtext ] !== 'undefined'){
						var text  = this.originaltext[ ij_indexOrigtext ];
					}else{
						var text  = el.innerHTML || el.innerText || el.value;
						this.originaltext[ ij_indexOrigtext ] = text;
					}
					
					this.regmatch = '';
					for(var k =0; k<regs.length; k++) {
						text = text.replace( 
								regs[k],
								// The interpreter expects a closure here, to bypass this we are wrapping
								// the result in another function e.g. 'return regmatch( arguments[0] );'
								// within the closure, functions wouldn't be called;
								// The first argument contains the entire match, the last the entire text;
								function(){
									return regmatch( arguments[0] );
								}
						);
					}
					if( CONFIG['isDebug'] ){
							console.log( text);
					}
					var strLimitForChg = 10;
					if(typeof el.innerHTML !== 'undefined'){
						this.htmlproptext = 'innerHTML';
							//did the text actually change?
						if( Math.abs( el.innerHTML.length - text.length) > strLimitForChg)
							el.innerHTML = text;
					} else if( typeof el.innerText !== 'undefined' ){
						this.htmlproptext = 'innerText';
						if( Math.abs( el.innerText.length - text.length) > strLimitForChg)
							el.innerText = text;
					} else if( typeof el.value !== 'undefined' ){
						this.htmlproptext = 'value';
						if( Math.abs( el.value.length - text.length) > strLimitForChg)
							el.value = text;
					}else
						return false;
				}
			}//end for
			return true;
		};
		this.init = init;
		//initialize and set the status
		this.intStatus = init();
		this.reinit = init;
	}


    // public static 
	clsKb.highlightKeys = function(e){
		var charInt = e.keyCode ? e.keyCode : e.charCode
		
		if( CONFIG['isDebug'] ){
				console.log( charInt, e.ctrlKey, e  );
		}
		//is event key up or down?
		if(e.type === 'keydown' ){
			if( CONFIG['isDebug'] )
				console.log(KeyBoarder.keyCodeToKey(e.keyCode), KEYMAPflip);
			//evaluates to: if(  e.keyCode == + CONFIG.KEYMAP['STRG'] ){
			//keylit: keyliteral...contains the literal key-name
			if( keylit = KeyBoarder.keyCodeToKey(e.keyCode) ){
				var i = KEYMAPIDX[keylit];
				var ele =  document.getElementsByClassName('kb'+keylit.toUpperCase())
				if(!ele.length) 
					return
				//add class, and scroll to the element
				csscls.add( 'kbKeyHighlight',ele[i]).focus(ele[i]);
				if(KEYMAPIDX[keylit]+1 < ele.length)
					KEYMAPIDX[keylit]++;
				else
					KEYMAPIDX[keylit] = 0; //reset, begin at the first element
			}
			
		}else
		if(e.type === 'keyup' ){
			//evaluates to: if(  e.keyCode == + CONFIG.KEYMAP['STRG'] ){
			if( keylit = KeyBoarder.keyCodeToKey(e.keyCode) ){
				var ele =  document.getElementsByClassName('kb'+keylit.toUpperCase())
				if(!ele.length) 
					return
				var i = KEYMAPIDX[keylit] === 0 ? ele.length-1 : KEYMAPIDX[keylit]-1; //remove current css-class
				csscls.del( 'kbKeyHighlight', ele[i]);
			}
		}
		//prevent propagation along the DOM tree
		e.cancelBubble = true;
	}
	//returns a literal key from a key code
	clsKb.keyCodeToKey = function(keyCode){
		return KEYMAPflip[keyCode].toLowerCase();
	}
	
	//private static
	//returns the ASCII key code
	function keyCode(n) {
		if (n === null) {
			return 'undefined';
		}
		return String.fromCharCode(n)
	}

    // public (across instances)
	//serialization override, which outputs info e.g. ''+kb
    clsKb.prototype = {	
		toString : function(){
			return __info__();
		},
    };

    return clsKb;
})(); 
//var kb = new KeyBoarder(kbparams);

}//end with



//INIT,- meant for loading at the bottom at the document
(function(that) {
	//check if the script is already loaded:
	var elScript = document.getElementsByTagName("script");
	for(var i = 0; i<elScript.length; i++) {
		if( /KeyBoarder/ig.test(elScript[i].src) ){
			//throw new Error("KeyBoarder has already been loaded in another script element tag");
		}
	}
	if( typeof KeyBoarder === 'undefined') {
		throw new TypeError("A variable or object with the name KeyBoarder does not (yet) exist in the global scope.");
	}else{
		//TODO: error handling
		window.addEventListener("error", function(e){console.error("KeyBoarder-Error:", e)} );
		//example of how to initiate
		/* Opera converts the addEventListener inline, thus not allowing string concatenation*/
		if(/opera/i.test(navigator.userAgent )) //navigator.taintEnabled conveniently checks for Mozilla browsers
			window.addEventListener("DOMContentLoaded", function(e){ var kb = new KeyBoarder(kbparams); }, null ); //opera 11x exclusively requires newer event-conventions
			//document.addEventListener("domcontentready", function(e){ var kb = new KeyBoarder(kbparams); } ); // document.ondomcontentloaded 
		else
			window.addEventListener("load", function(e){ var kb = new KeyBoarder(kbparams); } );
		//var kb = new KeyBoarder( ["content", "claro"] );
		
	}
})(window);