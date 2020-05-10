(require 'subr-x)
(setq org-export-with-smart-quotes t)
(setq org-export-with-timestamps t)
(setq-default org-html-with-latex t)
(setq org-export-use-babel t)
(setq org-global-properties
       '(("header-args" . ":exports both :eval no-export :noweb no-export")))
(setq org-html-htmlize-output-type 'css)
(setq org-publish-project-alist
      '(
	("org-to-html"
	 :base-directory ""
	 :publishing-directory ""
	 :publishing-function org-html-publish-to-html
	 :section-numbers t
	 :with-title nil
	 :html-head    "<link rel='stylesheet' type='text/css' href='/css/syntax.css'>
	 <link rel='stylesheet' type='text/css' href='/css/main.css'>"
	 :recursive t
	 :with-toc t
	 :html-toc-no-heading t
	)
                                        ;("supporting"
                                        ; :base-directory ""
                                        ; :base-extension "png\\|jpg\\|css\\|html\\|py"
                                        ; :publishing-directory ""
                                        ; :publishing-function org-publish-attachment
                                        ; :recursive t)
	))
; 
(setq org-html-preamble-format
      '(("en"
	 "
<div class='site-header'>
  <a class='site-title' href='/'>R E I N D E E R E F F E C T</a>
  <div class='nav' style='float:right;'>
    <a class='page-link' href='/about.html'>About</a>&nbsp;
    <a class='page-link' href='/links.html'>Links</a>&nbsp;
    <a class='page-link' href='/tags.html'>Tags</a>
  </div>
  <hr style='height:0.5px'>
</div>
<div class='post-head'>
  <div class='post-pubdate'>%d</div>
  <h1 class='title'>%t</h1>
</div>
 ")))

(setq org-export-date-timestamp-format "%Y-%m-%d")
(require 'ox-html)

;; Adding keyword TOC_NO_HEADING to html export keywords:
(push '(:html-toc-no-heading "TOC_NO_HEADING" nil nil t)
      (org-export-backend-options (org-export-get-backend 'html)))

(defun my-org-html-toc-no-heading (args)
  "Avoid toc heading in html export if the keyword TOC_HO_HEADING is t or yes.
 Works as a :filter-args advice for `org-html-toc' with argument list ARGS."
  (let* ((depth (nth 0 args))
         (info (nth 1 args))
         (scope (nth 2 args)))
    (when (and (assoc-string (plist-get info :html-toc-no-heading)
                             '(t yes)
                             t)
               (null scope))
      (setq scope (plist-get info :parse-tree)))
    (list depth info scope)))

(advice-add 'org-html-toc :filter-args #'my-org-html-toc-no-heading)
(defun re-org-html-postamble (plist)
  "<hr style='height:0.5px'>
<small>R E I N D E E R E F F E C T</small>")

(setq org-html-postamble 're-org-html-postamble)
(defun my-org-html-format-headline-function
    (todo todo-type priority text tags info)
  "Format a headline with a link to itself."
  (let* ((headline (get-text-property 0 :parent text))
         (id (or (org-element-property :CUSTOM_ID headline)
                 ;; (org-export-get-reference headline info)
                 (org-element-property :ID headline)))
         (link (if id
                   (format "<a href=\"#%s\">%s</a>" id text)
                 text))
         (default-format 'org-html-format-headline-default-function))
    (org-html-format-headline-default-function todo todo-type priority link tags info)))

(setq org-html-format-headline-function 'my-org-html-format-headline-function)
(defun src->block-name (src)
  (org-element-property :name src))

(defun src->block-id (src)
  (org-element-property :begin src))

(defun src->def (src)
  (cons (src->block-name src)
	(src->block-id src)))
(setq block-defs '())

(defun init-block-defs ()
  (setq block-defs
	(org-element-map
	    (org-element-parse-buffer)
	    'src-block
	  'src->def)))
(defun src->block-ids (src)
  (let ((name (org-element-property :name src)))
    (mapcar 'cdr (seq-filter (lambda (x)
			       (string= (car x) name))
			     block-defs))))

(defun src->prev-block-id (src)
  (let* ((id0 (src->block-id src))
	 (ids (seq-filter (lambda (id)
			    (< id id0))
			  (src->block-ids src))))
    (when ids (apply 'max ids))))

(defun src->next-block-id (src)
  (let* ((id0 (src->block-id src))
	 (ids (seq-filter (lambda (id)
			    (> id id0))
			  (src->block-ids src))))
    (when ids (apply 'min ids))))

(defun src->first-block-id (src)
  (apply 'min (src->block-ids src)))
(add-hook 'org-export-before-parsing-hook
          (lambda (backend) (init-block-defs)))
(defun noweb-links (src)
  (replace-regexp-in-string
   "&lt;&lt;\\([^&]+\\)&gt;&gt;"
   "&langle;<a class='noweb-ref' href='#\\1'>\\1</a>&rangle;"
   src))
(defun indent (src)
  (replace-regexp-in-string "^" "  " src))

(defun block-intro (src)
  (let* ((name (src->block-name src))
         (label (format "%s-%s" name (src->block-id src)))
         (next (src->next-block-id src))
         (next-link (if next
                        (format "<a href='#%s-%s'>&darr;</a>" name next)
                      ""))
         (prev (src->prev-block-id src))
         (prev-link (if prev
                        (format "<a href='#%s-%s'>&uarr;</a>" name prev)
                      ""))
         (chunk-nav (format "<span class='chunk-chain'>%s%s</span>"
                            prev-link
                            next-link)))
    (if name
        (if prev
            (format
             "<div id='%s'>&langle;<a href='#%s' class='noweb-ref'>%s</a>&rangle; +&equiv; %s</div>"
             label
             name
             name chunk-nav)
          (format
           "<div id='%s'>&langle;<span class='noweb-def' id='%s'>%s</span>&rangle; &equiv; %s</div>"
           name
           label
           name chunk-nav))
      "")))	  

(defun block-caption (src-block info)
  (let ((caption (org-export-get-caption src-block)))
    (if (not caption) ""
      (let ((listing-number
             (format
              "<span class=\"listing-number\">%s </span>"
              (format
               (org-html--translate "Listing %d:" info)
               (org-export-get-ordinal
                src-block info nil #'org-html--has-caption-p)))))
        (format "<label class=\"org-src-name\">%s%s</label>"
                listing-number
                (org-trim (org-export-data caption info)))))))

(defun block-label (src-block info)
  (let ((lbl (and (org-element-property :name src-block)
                  (org-export-get-reference src-block info))))
    (if lbl (format " id=\"%s\"" lbl) "")))

(defun org-html-src-block (src-block _contents info)
  "Transcode a SRC-BLOCK element from Org to HTML.
 CONTENTS holds the contents of the item.  INFO is a plist holding
 contextual information."
  (if (org-export-read-attribute :attr_html src-block :textarea)
      (org-html--textarea-block src-block)
    (let* ((lang (org-element-property :language src-block))
           (name (org-element-property :name src-block))
           (intro (block-intro src-block))
           (code (org-html-format-code src-block info))
           (fixed-code (string-trim-right (noweb-links (if (string= intro "")
                                                           code
                                                         (indent code)))))
           (label (block-label src-block info)))
      (if (not lang)
          (format "<pre class=\"example\"%s>%s</pre>" label code)
        (format "<div class=\"org-src-container\">\n%s%s\n</div>"
                (block-caption src-block info)
                (format "<pre class=\"src src-%s\"%s>%s%s</pre>"
                        lang 
                        label
                        intro
                        fixed-code))))))
