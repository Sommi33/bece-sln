from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# Initialize Widescreen Presentation
prs = Presentation()
prs.slide_width = Inches(13.33)  
prs.slide_height = Inches(7.5)

# Premium Color Palette (Dark Theme Tech Dashboard)
COLOR_BG = RGBColor(11, 11, 14)       # Deep Obsidian
COLOR_CARD = RGBColor(22, 22, 29)     # Sleek Slate Gray for containers
COLOR_TEXT_MAIN = RGBColor(240, 244, 241) # Soft Crisp White
COLOR_ACCENT = RGBColor(222, 255, 154)    # Technical Lime Green
COLOR_MUTED = RGBColor(150, 165, 155)     # Sage Gray
COLOR_ALERT_BG = RGBColor(45, 20, 20)     # Muted Crimson tint
COLOR_ALERT_TXT = RGBColor(255, 138, 138) # Light Coral

def apply_background(slide):
    """Sets a premium dark solid fill for the slide background."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_BG

def create_card(slide, left, top, width, height, bg_color=COLOR_CARD):
    """Draws a clean layout container card for grouping information."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.color.rgb = RGBColor(40, 40, 50)
    shape.line.width = Pt(1)
    return shape

def add_header(slide, title_text):
    """Adds a sharp, consistent localized header layout line."""
    box = slide.shapes.add_textbox(Inches(0.75), Inches(0.5), Inches(11.83), Inches(0.8))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text.upper()
    p.font.name = 'Urbanist'
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.font.letter_spacing = Pt(2)

# ==========================================
# SLIDE 1: PREMIUM TITLE SLIDE
# ==========================================
slide_layout = prs.slide_layouts[6] 
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)

# Draw decorative accent block
accent_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.75), Inches(2.2), Inches(0.15), Inches(3.2))
accent_bar.fill.solid()
accent_bar.fill.fore_color.rgb = COLOR_ACCENT
accent_bar.line.fill.background()

title_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.0), Inches(11.0), Inches(4.5))
tf = title_box.text_frame
tf.word_wrap = True

p1 = tf.paragraphs[0]
p1.text = "SOCIAL LEARNING NETWORKS"
p1.font.name = 'Urbanist'
p1.font.size = Pt(56)
p1.font.bold = True
p1.font.color.rgb = COLOR_TEXT_MAIN

p2 = tf.add_paragraph()
p2.text = "Using Graph Analytics to Optimize Peer Learning and Knowledge Diffusion in BECE Preparation"
p2.font.name = 'Urbanist'
p2.font.size = Pt(22)
p2.font.color.rgb = COLOR_ACCENT
p2.space_before = Pt(14)

p3 = tf.add_paragraph()
p3.text = "\nPresented by: Samuel Pelumi, Adebayo Eyitayo, Chisom Deborah, Semilore\nSupervisor: Dr. T. V. Igbe | Department of CS & IT | Redeemer's University"
p3.font.name = 'Urbanist'
p3.font.size = Pt(16)
p3.font.color.rgb = COLOR_MUTED

# ==========================================
# SLIDE 2: TWO-COLUMN ROADMAP
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)
add_header(slide, "Presentation Roadmap")

# Left Column Card
create_card(slide, Inches(0.75), Inches(1.8), Inches(5.6), Inches(4.8))
tf_left = slide.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.1), Inches(4.4)).text_frame
tf_left.word_wrap = True

left_items = ["01. Research Context", "02. Problem Statement", "03. Project Objectives", "04. Methodology Stack", "05. Graph Construction"]
for idx, item in enumerate(left_items):
    p = tf_left.paragraphs[0] if idx == 0 else tf_left.add_paragraph()
    p.text = item
    p.font.name = 'Urbanist'
    p.font.size = Pt(22)
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.space_after = Pt(18)

# Right Column Card
create_card(slide, Inches(6.98), Inches(1.8), Inches(5.6), Inches(4.8))
tf_right = slide.shapes.add_textbox(Inches(7.23), Inches(2.0), Inches(5.1), Inches(4.4)).text_frame
tf_right.word_wrap = True

right_items = ["06. Chapter 4: Hotspot Results", "07. Chapter 4: Diffusion Modeling", "08. Chapter 4: Group Optimization", "09. Chapter 5: Conclusions", "10. Key References"]
for idx, item in enumerate(right_items):
    p = tf_right.paragraphs[0] if idx == 0 else tf_right.add_paragraph()
    p.text = item
    p.font.name = 'Urbanist'
    p.font.size = Pt(22)
    p.font.color.rgb = COLOR_ACCENT
    p.space_after = Pt(18)

# ==========================================
# SLIDE 3: PROBLEM STATEMENT GRID (2x2 CARDS)
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)
add_header(slide, "Statement of the Problem")

problems = [
    ("Flawed Group Formations", "Study groups form via proximity or friendships, matching identical learning gaps instead of strengths."),
    ("Analytical Blindness", "Instructors possess no mathematical models to track knowledge diffusion paths or trace exchange speed."),
    ("Static Data Repositories", "Past question archives are processed as standard reading tasks rather than parsed for concept links."),
    ("Siloed Class Frameworks", "Without optimization, classroom peer structures reinforce collective misunderstandings instead of tutoring loops.")
]

card_w, card_h = Inches(5.6), Inches(2.2)
coords = [(Inches(0.75), Inches(1.8)), (Inches(6.98), Inches(1.8)), (Inches(0.75), Inches(4.4)), (Inches(6.98), Inches(4.4))]

for idx, (title, desc) in enumerate(problems):
    x, y = coords[idx]
    create_card(slide, x, y, card_w, card_h)
    tf = slide.shapes.add_textbox(x + Inches(0.2), y + Inches(0.2), card_w - Inches(0.4), card_h - Inches(0.4)).text_frame
    tf.word_wrap = True
    
    p1 = tf.paragraphs[0]
    p1.text = "⚠️ " + title
    p1.font.bold = True
    p1.font.size = Pt(20)
    p1.font.color.rgb = COLOR_ACCENT
    
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.size = Pt(16)
    p2.font.color.rgb = COLOR_MUTED
    p2.space_before = Pt(8)

# ==========================================
# SLIDE 4: OBJECTIVES GRID (1x4 SLATS)
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)
add_header(slide, "Specific Research Objectives")

objectives = [
    ("01 / CLASSIFICATION", "Categorize historical exam past questions by topic metrics and structural difficulty lines."),
    ("02 / HOTSPOT ANALYSIS", "Analyze responses systematically to map conceptual failures and performance trends."),
    ("03 / DEPENDENCY MODEL", "Build a predictive framework to isolate hidden interdisciplinary topic connections."),
    ("04 / PEER OPTIMIZATION", "Formulate an automated, diverse team selection framework utilizing machine learning clustering.")
]

for idx, (title, desc) in enumerate(objectives):
    y_pos = Inches(1.8 + (idx * 1.3))
    create_card(slide, Inches(0.75), y_pos, Inches(11.83), Inches(1.1))
    tf = slide.shapes.add_textbox(Inches(0.95), y_pos + Inches(0.15), Inches(11.43), Inches(0.8)).text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = title + "  —  "
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = COLOR_ACCENT
    
    run = p.add_run()
    run.text = desc
    run.font.bold = False
    run.font.color.rgb = COLOR_TEXT_MAIN

# ==========================================
# SLIDE 5: VISUAL HOTSPOTS WITH SHAPE BARS (CHAPTER 4)
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)
add_header(slide, "Chapter 4: Class Performance Hotspots")

hotspot_data = [
    ("West African History", 0.408),
    ("Commerce and Trade", 0.409),
    ("Linear Inequalities", 0.420),
    ("Technical Drawing", 0.401),
    ("English Studies Aggregate", 0.510)
]

# Side card for contextual explanation
create_card(slide, Inches(0.75), Inches(1.8), Inches(4.0), Inches(4.9))
tf_side = slide.shapes.add_textbox(Inches(0.95), Inches(2.0), Inches(3.6), Inches(4.5)).text_frame
tf_side.word_wrap = True
p_side = tf_side.paragraphs[0]
p_side.text = "Hotspot Diagnostic Analysis"
p_side.font.bold = True
p_side.font.size = Pt(20)
p_side.font.color.rgb = COLOR_ACCENT

p_side2 = tf_side.add_paragraph()
p_side2.text = "\nGaps were isolated using an empirical failure threshold set at 40%.\n\nEvery top bottleneck tracks directly into the Hard tier, validating the expertise of the question categorization bank."
p_side2.font.size = Pt(16)
p_side2.font.color.rgb = COLOR_TEXT_MAIN

# Draw data chart using loops and shapes
for idx, (label, val) in enumerate(hotspot_data):
    y_pos = Inches(1.8 + (idx * 1.0))
    
    # Text label box
    lbl_box = slide.shapes.add_textbox(Inches(5.0), y_pos, Inches(3.0), Inches(0.5))
    lbl_box.text_frame.paragraphs[0].text = label
    lbl_box.text_frame.paragraphs[0].font.size = Pt(16)
    lbl_box.text_frame.paragraphs[0].font.color.rgb = COLOR_TEXT_MAIN
    lbl_box.text_frame.paragraphs[0].font.bold = True
    
    # Base background tracking bar
    bg_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.2), y_pos + Inches(0.1), Inches(4.0), Inches(0.3))
    bg_bar.fill.solid()
    bg_bar.fill.fore_color.rgb = RGBColor(25, 25, 35)
    bg_bar.line.fill.background()
    
    # Foreground data bar representation
    fill_w = Inches(4.0 * val)
    fill_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8.2), y_pos + Inches(0.1), fill_w, Inches(0.3))
    fill_bar.fill.solid()
    fill_bar.fill.fore_color.rgb = COLOR_ACCENT if val < 0.45 else COLOR_MUTED
    fill_bar.line.fill.background()
    
    # Numerical overlay string
    val_box = slide.shapes.add_textbox(Inches(12.3), y_pos - Inches(0.05), Inches(0.8), Inches(0.4))
    val_box.text_frame.paragraphs[0].text = f"{val*100:.1f}%"
    val_box.text_frame.paragraphs[0].font.size = Pt(14)
    val_box.text_frame.paragraphs[0].font.color.rgb = COLOR_ACCENT if val < 0.45 else COLOR_MUTED

# ==========================================
# SLIDE 6: CRITICAL FINDING CALLOUT PANEL
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)
add_header(slide, "Chapter 4: The Core Theoretical Rule")

# Giant Red Warning Accent Callout Panel
create_card(slide, Inches(0.75), Inches(1.8), Inches(11.83), Inches(4.8), bg_color=COLOR_ALERT_BG)

tf_crit = slide.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(11.0), Inches(4.0)).text_frame
tf_crit.word_wrap = True

p1 = tf_crit.paragraphs[0]
p1.text = "🚨 CASE STUDY: TECHNICAL DRAWING DIFFUSION TIMELINE"
p1.font.bold = True
p1.font.size = Pt(24)
p1.font.color.rgb = COLOR_ALERT_TXT

p2 = tf_crit.add_paragraph()
p2.text = "\n• Baseline Assessment: Technical Drawing recorded a 100% conceptual gap parameter across testing clusters, meaning the initial seed population of knowledgeable students was absolute zero (I = 0.0)."
p2.font.size = Pt(18)
p2.font.color.rgb = COLOR_TEXT_MAIN
p2.space_after = Pt(12)

p3 = tf_crit.add_paragraph()
p3.text = "• The Outcome: Because there were no internal student seeds available to initiate peer tutoring tracks, the mathematical numerical model logged a flatlined 0.00% diffusion velocity across the entire 60-day tracking lifecycle."
p3.font.size = Pt(18)
p3.font.color.rgb = COLOR_TEXT_MAIN
p3.space_after = Pt(12)

p4 = tf_crit.add_paragraph()
p4.text = "• The Core Conclusion: Peer learning networks completely stall without basic human instruction. Collaborative study sessions cannot fix a performance bottleneck if zero nodes inside the group understand the syllabus material."
p4.font.bold = True
p4.font.size = Pt(18)
p4.font.color.rgb = COLOR_ALERT_TXT

# ==========================================
# SLIDE 7: BIG NUMBERS COMPLEMENTARITY INDEX
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)
add_header(slide, "Chapter 4: Diverse Matching Results")

# Massive Stat Block Left
stat_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.75), Inches(1.8), Inches(4.5), Inches(4.8))
stat_bg.fill.solid()
stat_bg.fill.fore_color.rgb = COLOR_CARD
stat_bg.line.color.rgb = RGBColor(40, 40, 50)

tf_stat = slide.shapes.add_textbox(Inches(0.85), Inches(2.4), Inches(4.3), Inches(3.5)).text_frame
tf_stat.word_wrap = True
p_num = tf_stat.paragraphs[0]
p_num.text = "+13.3%"
p_num.font.size = Pt(64)
p_num.font.bold = True
p_num.font.color.rgb = COLOR_ACCENT
p_num.alignment = PP_ALIGN.CENTER

p_lbl = tf_stat.add_paragraph()
p_lbl.text = "\nOptimization Delta Over Unstructured Groups"
p_lbl.font.size = Pt(18)
p_lbl.font.color.rgb = COLOR_TEXT_MAIN
p_lbl.alignment = PP_ALIGN.CENTER

# Explanatory Text Right Box
tf_desc = slide.shapes.add_textbox(Inches(5.8), Inches(1.8), Inches(6.8), Inches(4.8)).text_frame
tf_desc.word_wrap = True

bullets = [
    "Stratified Diversity Sampling: Traditional K-Means models aggregate identical competencies together. For peer tutoring, the exact opposite is required.",
    "The Solution Module: The pipeline utilizes clustering to divide capability layers into 5 distinct student archetypes, then extracts 1 student per archetype to form teams.",
    "Balanced Topologies: The matching engine produced 10 teams of 5 students, maximizing group variance to spark natural peer tutoring loops.",
    "Isolating Hub Learners: Profile calculations identified distinct students (e.g. STU034) who possess unique complementary traits, making them perfect assets across multiple study frames."
]

for idx, b in enumerate(bullets):
    p = tf_desc.paragraphs[0] if idx == 0 else tf_desc.add_paragraph()
    p.text = "• " + b
    p.font.size = Pt(18)
    p.font.color.rgb = COLOR_MUTED
    p.space_after = Pt(14)

# ==========================================
# SLIDE 8: CHAPTER 5 STRATEGIC roadMAP
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)
add_header(slide, "Chapter 5: Summary & Contributions")

# Split Horizontal Layout Blocks
create_card(slide, Inches(0.75), Inches(1.8), Inches(11.83), Inches(2.2))
tf_top = slide.shapes.add_textbox(Inches(0.95), Inches(2.0), Inches(11.43), Inches(1.8)).text_frame
tf_top.word_wrap = True

p_t1 = tf_top.paragraphs[0]
p_t1.text = "🎯 CORE EMPIRICAL FINDINGS SUMMARY"
p_t1.font.bold = True
p_t1.font.size = Pt(18)
p_t1.font.color.rgb = COLOR_ACCENT

p_t2 = tf_top.add_paragraph()
p_t2.text = "• 1,252 Predictive dependencies isolated across 3,160 curriculum tracks; 803 were cross-subject links, proving student failure trends are holistic rather than isolated within single subjects.\n• Diagnostic analysis proves that topic-level tracking isolates student capability metrics that general report grades completely obscure."
p_t2.font.size = Pt(16)
p_t2.font.color.rgb = COLOR_TEXT_MAIN
p_t2.space_before = Pt(6)

create_card(slide, Inches(0.75), Inches(4.4), Inches(11.83), Inches(2.2))
tf_bot = slide.shapes.add_textbox(Inches(0.95), Inches(4.6), Inches(11.43), Inches(1.8)).text_frame
tf_bot.word_wrap = True

p_b1 = tf_bot.paragraphs[0]
p_b1.text = "🎓 SYSTEM CONTRIBUTION TO KNOWLEDGE"
p_b1.font.bold = True
p_b1.font.size = Pt(18)
p_b1.font.color.rgb = COLOR_ACCENT

p_b2 = tf_bot.add_paragraph()
p_b2.text = "• Methodological Novelty: Introduces the first structural application of epidemiological differential equations to map knowledge diffusion speeds inside secondary schools.\n• Strategic Alternative: Replaces unoptimized, friendship-based clustering with a calculated decision-support matching tool."
p_b2.font.size = Pt(16)
p_b2.font.color.rgb = COLOR_TEXT_MAIN
p_b2.space_before = Pt(6)

# ==========================================
# SLIDE 9: LIMITATIONS & RECOMMENDATIONS FRAMEWORKS
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)
add_header(slide, "Chapter 5: Limitations & Future Work")

# Left Column (Limitations Card)
create_card(slide, Inches(0.75), Inches(1.8), Inches(5.6), Inches(4.8))
tf_lim = slide.shapes.add_textbox(Inches(0.95), Inches(2.0), Inches(5.2), Inches(4.4)).text_frame
tf_lim.word_wrap = True

p_lim = tf_lim.paragraphs[0]
p_lim.text = "⚠️ RESEARCH LIMITATIONS"
p_lim.font.bold = True
p_lim.font.size = Pt(18)
p_lim.font.color.rgb = RGBColor(255, 150, 150)

lims = [
    "Evaluated using synthetically generated class score matrices rather than a live classroom field test.",
    "Sample parameters bounded to 50 student profiles across 80 unique subject topic nodes.",
    "Theoretical configurations used for transmission variables (beta, gamma) due to a lack of empirical interaction tracking data."
]
for lim in lims:
    p = tf_lim.add_paragraph()
    p.text = "• " + lim
    p.font.size = Pt(16)
    p.font.color.rgb = COLOR_MUTED
    p.space_before = Pt(12)

# Right Column (Recommendations Card)
create_card(slide, Inches(6.98), Inches(1.8), Inches(5.6), Inches(4.8))
tf_rec = slide.shapes.add_textbox(Inches(7.18), Inches(2.0), Inches(5.2), Inches(4.4)).text_frame
tf_rec.word_wrap = True

p_rec = tf_rec.paragraphs[0]
p_rec.text = "🚀 FUTURE RECOMMENDATIONS"
p_rec.font.bold = True
p_rec.font.size = Pt(18)
p_rec.font.color.rgb = COLOR_ACCENT

recs = [
    "Vistaplus Integration: Link the API directly with evaluation dashboards to stream actual student test score parameters automatically.",
    "Constrained K-Means: Deploy algorithm variations that enforce strict, equal populations across all generated team shapes.",
    "Interface Expansion: Add student portals displaying personalized weakness metrics and real-time failure warning banner displays."
]
for rec in recs:
    p = tf_rec.add_paragraph()
    p.text = "• " + rec
    p.font.size = Pt(16)
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.space_before = Pt(12)

# ==========================================
# SLIDE 10: CLEAN BIBLIOGRAPHY LITERARY ENTRIES
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)
add_header(slide, "Key Literary References")

content_box = slide.shapes.add_textbox(Inches(0.75), Inches(1.8), Inches(11.83), Inches(5.0))
tf = content_box.text_frame
tf.word_wrap = True

refs = [
    "Barabási, A. L. (2016). Network science. Cambridge University Press.",
    "Esomonu, N. P. M., & Ogbuzulu, U. P. (2019). Students' grades in Basic Education Certificate Examination as predictor of grades in WASSCE. Applied Science and Innovative Research, 3(4), 304–315.",
    "Hogan, A., Blomqvist, E., Cochez, M., et al. (2021). Knowledge graphs. ACM Computing Surveys, 54(4), 1–37.",
    "Okpube, N. M., Ugama, J. O., Nnachi, N. O., & Anugwo, M. N. (2021). Predictive validity of achievement scores in BECE on achievement in SSCE. Journal of Education and Practice, 12(21), 19–28.",
    "Romero, C., & Ventura, S. (2010). Educational data mining: A review of the state of the art. IEEE Transactions on Systems, Man, and Cybernetics, 40(6), 601–618.",
    "Virtanen, P., Gommers, R., Oliphant, T. E., et al. (2020). SciPy 1.0: Fundamental algorithms for scientific computing in Python. Nature Methods, 17(3), 261–272."
]

for idx, ref in enumerate(refs):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.text = "• " + ref
    p.font.name = 'Urbanist'
    p.font.size = Pt(16)
    p.font.color.rgb = COLOR_MUTED
    p.space_after = Pt(14)

# ==========================================
# SLIDE 11: CLOSING THANK YOU PAGE
# ==========================================
slide = prs.slides.add_slide(slide_layout)
apply_background(slide)

title_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(11.33), Inches(3.0))
tf = title_box.text_frame
tf.word_wrap = True

p1 = tf.paragraphs[0]
p1.text = "THANK YOU"
p1.font.name = 'Urbanist'
p1.font.size = Pt(64)
p1.font.bold = True
p1.font.color.rgb = COLOR_ACCENT
p1.alignment = PP_ALIGN.CENTER

p2 = tf.add_paragraph()
p2.text = "Transforming BECE Preparation via Network Science Topologies\n\nWe welcome questions from the distinguished project defense committee."
p2.font.name = 'Urbanist'
p2.font.size = Pt(20)
p2.font.color.rgb = COLOR_TEXT_MAIN
p2.alignment = PP_ALIGN.CENTER
p2.space_before = Pt(10)

# Save presentation to working path area
prs.save("Premium_BECE_SLN_Defense_Deck.pptx")
print("SUCCESS: Executive boardroom presentation file compiled as 'Premium_BECE_SLN_Defense_Deck.pptx'!")