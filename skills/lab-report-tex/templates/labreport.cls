% labreport.cls —— 中文理工科实验报告文档类（XeLaTeX + ctex）
% 项目主页：https://github.com/ZhuZiheng66/lab-report-tex   许可：MIT
%
% 用法概览（完整示例见 templates/report.tex）：
%   \documentclass{labreport}            % 默认：带框章节（像学校 Word 模板的大表格）
%   \documentclass[plain]{labreport}     % 普通章节标题，无外框
%   \labset{ school=深圳大学, expname=..., cover=szu, ... }
%   \makecover
%   \begin{labsection}{实验目的} ... \end{labsection}
%   \labfig[12cm]{fig/a.png}{图题}  \labtable{表题}{...tabular...}
%   \labcomment  \labgrading{预习/20,操作及记录/40,数据处理与结果陈述/30,思考题/10}
%   \labphotos{原始数据}{raw/p1.jpg,raw/p2.jpg}
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{labreport}[2026/10/17 v1.0 Chinese lab report class]

\newif\iflab@framed \lab@framedtrue
\DeclareOption{plain}{\lab@framedfalse}
\DeclareOption{framed}{\lab@framedtrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{ctexart}}
\ProcessOptions\relax
\LoadClass[a4paper,zihao=5,UTF8,linespread=1.3]{ctexart}

\RequirePackage[top=2.4cm,bottom=2.4cm,left=2.3cm,right=2.3cm,footskip=1cm]{geometry}
\RequirePackage{amsmath,amssymb}
\RequirePackage{graphicx,array,booktabs,tabularx,multirow,makecell}
\RequirePackage{etoolbox,pgfkeys,xcolor}
\RequirePackage[most]{tcolorbox}
\RequirePackage{caption}
\RequirePackage{siunitx}
\RequirePackage{fancyhdr}
\RequirePackage[hidelinks]{hyperref}

% ---------- 字体：西文/数字用 Times New Roman（没有就用 TeX Gyre Termes），中文由 ctex 按系统自动选 ----------
\IfFontExistsTF{Times New Roman}
  {\setmainfont{Times New Roman}}
  {\IfFontExistsTF{TeX Gyre Termes}{\setmainfont{TeX Gyre Termes}}{}}

% ①②③ 等带圈数字按中文字体排（Times New Roman 里没有，不处理会变成空白）
\xeCJKDeclareCharClass{CJK}{"2460 -> "24FF, "2776 -> "2793}

% ---------- 数字、单位、图表题 ----------
\sisetup{
  separate-uncertainty = true,
  inter-unit-product   = \ensuremath{\cdot},
  exponent-product     = \times,
  group-digits         = false,
  output-decimal-marker= {.}
}
\captionsetup{font=small,labelsep=quad,skip=4pt}
\captionsetup[table]{position=top}
\renewcommand{\arraystretch}{1.25}
\setlength{\parindent}{2em}

% ---------- 页眉页脚 ----------
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0pt}

% ---------- 报告信息 ----------
\pgfkeys{/lab/.is family, /lab,
  school/.store in     = \lab@school,     school     = {},
  title/.store in      = \lab@title,      title      = {实验报告},
  coursename/.store in = \lab@coursename, coursename = {},
  coursecode/.store in = \lab@coursecode, coursecode = {},
  expname/.store in    = \lab@expname,    expname    = {},
  college/.store in    = \lab@college,    college    = {},
  major/.store in      = \lab@major,      major      = {},
  teacher/.store in    = \lab@teacher,    teacher    = {},
  author/.store in     = \lab@author,     author     = {},
  studentid/.store in  = \lab@studentid,  studentid  = {},
  group/.store in      = \lab@group,      group      = {},
  partner/.store in    = \lab@partner,    partner    = {},
  location/.store in   = \lab@location,   location   = {},
  date/.store in       = \lab@date,       date       = {},
  submitdate/.store in = \lab@submitdate, submitdate = {},
  cover/.store in      = \lab@cover,      cover      = {simple},
  scorebox/.is if      = lab@scorebox,
}
\newif\iflab@scorebox \lab@scoreboxtrue
\newcommand{\labset}[1]{\pgfkeys{/lab,#1}}
% 正文里引用：\labinfo{expname}
\newcommand{\labinfo}[1]{\csname lab@#1\endcsname}

% ---------- 封面 ----------
% 带下划线的定宽字段：\lab@field{标签}{内容}{下划线宽度}
\newcommand{\lab@label}[1]{\makebox[4.2em][s]{#1}：}
\newcommand{\lab@ul}[2]{\underline{\makebox[#1][c]{#2}}}
\newcommand{\lab@field}[3]{\lab@label{#1}\lab@ul{#3}{#2}}

\newcommand{\lab@scoretable}{%
  \begin{tabular}{|p{1.6cm}<{\centering}|p{1.9cm}<{\centering}|p{1.9cm}<{\centering}|}
    \hline 得分 & 教师签名 & 批改日期 \\ \hline
    \rule{0pt}{1.1cm} & & \\ \hline
  \end{tabular}}

% cover=szu：深圳大学实验报告封面样式（左上课程编号、右上得分栏、字距拉开的大标题）
\newcommand{\lab@cover@szu}{%
  \thispagestyle{empty}
  \noindent
  \begin{minipage}[b]{0.45\textwidth}\small 课程编号\lab@ul{3.2cm}{\lab@coursecode}\end{minipage}%
  \hfill\iflab@scorebox{\small\lab@scoretable}\fi
  \par\vspace{2.6cm}
  \begin{center}{\zihao{1}\bfseries\ziju{1.2}\lab@school\lab@title}\end{center}
  \vspace{1.6cm}
  {\zihao{4}\setlength{\parindent}{0pt}\linespread{2.2}\selectfont
  \hspace*{1.2cm}\parbox{13.5cm}{%
    \lab@field{课程名称}{\lab@coursename}{9.5cm}\par
    \lab@field{实验名称}{\lab@expname}{9.5cm}\par
    \lab@field{学院}{\lab@college}{9.5cm}\par
    \lab@field{指导教师}{\lab@teacher}{9.5cm}\par
    \lab@field{报告人}{\lab@author}{4.0cm}\quad 组号：\lab@ul{3.6cm}{\lab@group}\par
    \lab@field{学号}{\lab@studentid}{4.0cm}\quad 实验地点：\lab@ul{2.6cm}{\lab@location}\par
    \lab@field{实验时间}{\lab@date}{9.5cm}\par
    \lab@field{提交时间}{\lab@submitdate}{9.5cm}\par}}
  \clearpage}

% cover=simple：通用封面（居中标题 + 信息表），任何学校可用
\newcommand{\lab@cover@simple}{%
  \thispagestyle{empty}
  \iflab@scorebox\hfill{\small\lab@scoretable}\par\fi
  \vspace*{3cm}
  \begin{center}
    {\zihao{1}\bfseries\ziju{0.6}\lab@school\lab@title\par}
    \vspace{0.8cm}
    {\zihao{3}\lab@expname\par}
    \vspace{2cm}
    {\zihao{4}\linespread{2.0}\selectfont
    \begin{tabular}{@{}r@{}l@{}}
      \ifdefempty{\lab@coursename}{}{\lab@label{课程名称} & \lab@ul{7.5cm}{\lab@coursename}\\}
      \ifdefempty{\lab@college}{}{\lab@label{学院} & \lab@ul{7.5cm}{\lab@college}\\}
      \ifdefempty{\lab@major}{}{\lab@label{专业} & \lab@ul{7.5cm}{\lab@major}\\}
      \lab@label{姓名} & \lab@ul{7.5cm}{\lab@author}\\
      \ifdefempty{\lab@studentid}{}{\lab@label{学号} & \lab@ul{7.5cm}{\lab@studentid}\\}
      \ifdefempty{\lab@group}{}{\lab@label{组号} & \lab@ul{7.5cm}{\lab@group}\\}
      \ifdefempty{\lab@partner}{}{\lab@label{同组者} & \lab@ul{7.5cm}{\lab@partner}\\}
      \ifdefempty{\lab@teacher}{}{\lab@label{指导教师} & \lab@ul{7.5cm}{\lab@teacher}\\}
      \ifdefempty{\lab@location}{}{\lab@label{实验地点} & \lab@ul{7.5cm}{\lab@location}\\}
      \lab@label{实验时间} & \lab@ul{7.5cm}{\lab@date}\\
      \ifdefempty{\lab@submitdate}{}{\lab@label{提交时间} & \lab@ul{7.5cm}{\lab@submitdate}\\}
    \end{tabular}\par}
  \end{center}
  \clearpage}

\newcommand{\makecover}{%
  \hypersetup{pdftitle={\lab@expname}, pdfauthor={\lab@author}}%
  \ifcsdef{lab@cover@\lab@cover}
    {\csname lab@cover@\lab@cover\endcsname}
    {\ClassError{labreport}{Unknown cover style `\lab@cover'}{Use cover=szu or cover=simple}}%
  \setcounter{page}{1}}

% ---------- 章节 ----------
% 带框模式：每章一个可跨页的框，上下框线相接，效果接近学校模板的大表格。
% 框内不能放浮动体，所以图表一律用 \labfig / \labtable（或 [H] 之外的 \captionof）。
\newcounter{labsec}
\tcbset{lab@frame/.style={enhanced,breakable,sharp corners,boxrule=0.5pt,
  colback=white,colframe=black,left=6pt,right=6pt,top=4pt,bottom=6pt,
  before skip=0pt,after skip=0pt,parbox=false}}
\newcommand{\lab@secfont}{\bfseries\zihao{-4}}
\newcommand{\lab@sectitle}[1]{{\lab@secfont #1\par}\vspace{2pt}}

\iflab@framed
  \newtcolorbox{lab@box}{lab@frame}
  \newenvironment{labsection}[1]
    {\refstepcounter{labsec}\par\noindent\begin{lab@box}\setlength{\parindent}{2em}%
     \noindent\lab@sectitle{\chinese{labsec}、#1}}
    {\end{lab@box}\par\nointerlineskip\vspace{-0.5pt}}
  % 不编号的框（教师评阅意见等）
  \newenvironment{labsection*}[1]
    {\par\noindent\begin{lab@box}\setlength{\parindent}{2em}\noindent\lab@sectitle{#1}}
    {\end{lab@box}\par\nointerlineskip\vspace{-0.5pt}}
  % 不可拆分的框（评阅意见、评分栏：标题和内容必须在同一页）
  \newtcolorbox{lab@ubox}{lab@frame,unbreakable}
  \newenvironment{lab@block}[1]
    {\par\noindent\begin{lab@ubox}\setlength{\parindent}{2em}\noindent\lab@sectitle{#1}}
    {\end{lab@ubox}\par\nointerlineskip\vspace{-0.5pt}}
\else
  \newenvironment{labsection}[1]
    {\refstepcounter{labsec}\section*{\chinese{labsec}、#1}}{\par}
  \newenvironment{labsection*}[1]{\section*{#1}}{\par}
  \newenvironment{lab@block}[1]
    {\par\addvspace{1.2ex}\noindent\begin{minipage}{\linewidth}{\lab@secfont #1\par}\vspace{0.8ex}}
    {\end{minipage}\par}
\fi
\ctexset{section={format=\lab@secfont\raggedright,beforeskip=1.2ex,afterskip=0.8ex}}
% 小节：（一）（二）
\newcounter{labsub}[labsec]
\newcommand{\labsub}[1]{\par\addvspace{4pt}\stepcounter{labsub}%
  \noindent{\bfseries （\chinese{labsub}）#1}\par\addvspace{2pt}}

% ---------- 图表（非浮动，框内框外都能用） ----------
% \labfig[宽度]{文件}{图题}[label]
\NewDocumentCommand{\labfig}{O{0.72\linewidth} m m o}{%
  \par\addvspace{6pt}\noindent\begin{minipage}{\linewidth}\centering
  \includegraphics[width=#1,height=0.42\textheight,keepaspectratio]{#2}\par
  \captionof{figure}{#3}\IfValueT{#4}{\label{#4}}\end{minipage}\par\addvspace{6pt}}
% \labfigs{文件1}{图题1}{label1}{文件2}{图题2}{label2}：两张小图并排（label 可留空 {}）
\newcommand{\labfigs}[6]{%
  \par\addvspace{6pt}\noindent
  \begin{minipage}[t]{0.49\linewidth}\centering
    \includegraphics[width=\linewidth,height=0.3\textheight,keepaspectratio]{#1}\par
    \captionof{figure}{#2}\ifstrempty{#3}{}{\label{#3}}\end{minipage}\hfill
  \begin{minipage}[t]{0.49\linewidth}\centering
    \includegraphics[width=\linewidth,height=0.3\textheight,keepaspectratio]{#4}\par
    \captionof{figure}{#5}\ifstrempty{#6}{}{\label{#6}}\end{minipage}\par\addvspace{6pt}}
% \labtable{表题}[label]{表格内容（tabular 等）}；表题和表格包在一起，不会被分页拆开
\NewDocumentCommand{\labtable}{m o +m}{%
  \par\addvspace{6pt}\noindent\begin{minipage}{\linewidth}\centering
  \captionof{table}{#1}\IfValueT{#2}{\label{#2}}\par
  {\small #3}\end{minipage}\par\addvspace{6pt}}
\renewcommand{\thefigure}{\arabic{figure}}
\renewcommand{\thetable}{\arabic{table}}

% 题目 + 答：\question{题目}  答案正文
\newcounter{labq}
\newcommand{\question}[1]{\par\addvspace{4pt}\stepcounter{labq}%
  \noindent{\bfseries\thelabq．#1}\par\noindent 答：}

% ---------- 教师评阅、评分栏 ----------
\newcommand{\labcomment}[1][3.5cm]{%
  \begin{lab@block}{指导教师批阅意见}\vspace*{#1}\end{lab@block}}

\newcommand{\lab@ghead}{}\newcommand{\lab@gblank}{}\newcounter{lab@gn}
\def\lab@gsplit#1/#2\@nil{%
  \appto\lab@ghead{#1\newline（#2分）&}\appto\lab@gblank{&}\stepcounter{lab@gn}}
\newcommand{\lab@gadd}[1]{\lab@gsplit#1\@nil}
% \labgrading[额外列]{项目/分值,...}；默认再加“报告整体印象”“总分”两列
\newcount\lab@gxn
\newcommand{\lab@gextra}{}\newcommand{\lab@gextrablank}{}
\newcommand{\lab@gx}[1]{%
  \ifnum\lab@gxn=0 \appto\lab@gextra{#1}\else\appto\lab@gextra{&#1}\appto\lab@gextrablank{&}\fi
  \advance\lab@gxn by 1 }
\newcommand{\labgrading}[2][报告整体印象,总分]{%
  \renewcommand{\lab@ghead}{}\renewcommand{\lab@gblank}{}\setcounter{lab@gn}{0}%
  \renewcommand{\lab@gextra}{}\renewcommand{\lab@gextrablank}{}\lab@gxn=0
  \forcsvlist{\lab@gadd}{#2}%
  \forcsvlist{\lab@gx}{#1}%
  \begin{lab@block}{成绩评定}
    \par\vspace{4pt}{\centering\small\noindent
    \begin{tabularx}{\linewidth}{|*{\numexpr\value{lab@gn}+\lab@gxn\relax}{>{\centering\arraybackslash}X|}}
      \hline \lab@ghead\lab@gextra \\ \hline
      \rule{0pt}{1.2cm}\lab@gblank\lab@gextrablank \\ \hline
    \end{tabularx}\par}\vspace{6pt}
  \end{lab@block}}

% ---------- 照片页（原始数据、预习试卷等，各占一页） ----------
% \labphotos{页标题，可留空}{a.jpg,b.jpg}；照片先用 scripts/prep_photos.py 转正、压缩
\newcommand{\lab@photo}[2]{%
  \clearpage
  {\centering\setlength{\parindent}{0pt}%
    \ifstrempty{#1}{}{{\bfseries\zihao{4}#1}\par\vspace{0.4em}}%
    \includegraphics[width=\textwidth,height=\dimexpr\textheight-3em\relax,keepaspectratio]{#2}\par}}
\newcommand{\labphotos}[2]{\forcsvlist{\lab@photo{#1}}{#2}\clearpage}

\endinput
