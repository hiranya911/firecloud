;;; init.el --- Emacs initialization file.

;;; Commentary:

;;; Emacs config by Hiranya Jayathilaka.

;;; Code:


;; Stop creating backup~ files
(setq make-backup-files nil)


;; Stop creating #autosave# files
;(setq auto-save-default nil)


(require 'package)
(let* ((no-ssl (and (memq system-type '(windows-nt ms-dos))
		    (not (gnutls-available-p))))
       (proto (if no-ssl "http" "https")))
  (when no-ssl
        (warn "\
Your version of Emacs does not support SSL connections,
which is unsafe because it allows man-in-the-middle attacks.
There are two things you can do about this warning:
1. Install an Emacs version that does support SSL and be safe.
2. Remove this warning from your init file so you won't see it again."))
  ;; Comment/uncomment these two lines to enable/disable MELPA and MELPA Stable as desired
  (add-to-list 'package-archives (cons "melpa" (concat proto "://melpa.org/packages/")) t)
  ;;(add-to-list 'package-archives (cons "melpa-stable" (concat proto "://stable.melpa.org/packages/")) t)
  (when (< emacs-major-version 24)
    ;; For important compatibility libraries like cl-lib
    (add-to-list 'package-archives (cons "gnu" (concat proto "://elpa.gnu.org/packages/")))))
(package-initialize)


;; Set theme and font defaults
(custom-set-variables
 '(custom-enabled-themes (quote (deeper-blue))))
(custom-set-faces
 '(default ((t (:family "Ubuntu Mono" :foundry "DAMA" :slant normal :weight normal :height 151 :width normal)))))


;; Maximize on launch
(add-to-list 'default-frame-alist '(fullscreen . maximized))


;; Disable splash screen and startup message
(setq inhibit-startup-message t)
(setq initial-scratch-message nil)


;; Hide the toolbar
(menu-bar-mode -1)


;; TypeScript configuration
(defun setup-tide-mode ()
  (interactive)
  (tide-setup)
  (flycheck-mode +1)
  (setq flycheck-check-syntax-automatically '(save mode-enabled))
  (eldoc-mode +1)
  (tide-hl-identifier-mode +1)
  ;; aligns annotation to the right hand side
  (setq company-tooltip-align-annotations t)
  ;; formats the buffer before saving
  (add-hook 'before-save-hook 'tide-format-before-save))
(add-hook 'typescript-mode-hook #'setup-tide-mode)


;; Python configuration
(defun py-mode-setup()
  (electric-pair-mode 1))
(add-hook 'python-mode-hook 'jedi:setup)
(add-hook 'python-mode-hook 'py-mode-setup)


;; Golang configuration
(defun go-mode-setup ()
  "Set up the Golang mode."
  (linum-mode 1)
  (electric-pair-mode 1)
  (subword-mode 1)
  (go-eldoc-setup)
  (setq gofmt-command "goimports")
  (add-hook 'before-save-hook 'gofmt-before-save)
  (local-set-key (kbd "M-.") 'godef-jump)
  (make-local-variable 'compile-command)
  (setq compile-command "go build -v && echo Testing... && go test -test.short -v && golint -set_exit_status")
  (require 'go-autocomplete)
  (add-to-list 'load-path (concat (getenv "GOPATH")  "/src/github.com/golang/lint/misc/emacs"))
  (require 'golint)
  (make-local-variable 'compilation-read-command)
  (setq compilation-read-command nil))
(add-hook 'go-mode-hook 'go-mode-setup)


;; Load auto-complete
(ac-config-default)
(require 'auto-complete-config)


;; Smaller compilation buffer
(setq compilation-window-height 14)
(setq compilation-scroll-output t)
(defun my-compilation-hook ()
  "Make the compilation window small."
  (when (not (get-buffer-window "*compilation*"))
    (save-selected-window
      (save-excursion
        (let* ((w (split-window-vertically))
               (h (window-height w)))
          (select-window w)
          (switch-to-buffer "*compilation*")
          (shrink-window (- h compilation-window-height)))))))
(add-hook 'compilation-mode-hook 'my-compilation-hook)


;; Close compilation buffer if no errors
(setq compilation-finish-function
  (lambda (buf str)
    (if (null (string-match ".*exited abnormally.*" str))
        ;;no errors, make the compilation window go away in a few seconds
        (progn
          (run-at-time
           "2 sec" nil 'delete-windows-on
           (get-buffer-create "*compilation*"))
          (message "No Compilation Errors!")))))


;; Toggle comment region
(global-set-key (kbd "C-c C-c") 'comment-or-uncomment-region)


(defun toggle-comment-on-line ()
  "Comment or uncomment current line."
  (interactive)
  (comment-or-uncomment-region (line-beginning-position) (line-end-position)))
(global-set-key (kbd "C-c C-l") 'toggle-comment-on-line)


;; Launch term
(global-set-key (kbd "C-c t") '(lambda ()  (interactive) (ansi-term "/bin/bash")))


;; Wrap in double quotes
(global-set-key (kbd "M-\"") 'insert-pair)


;;; init.el ends here
