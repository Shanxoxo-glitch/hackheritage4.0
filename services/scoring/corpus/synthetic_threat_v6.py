import pandas as pd


OUTPUT_PATH = "training/data/threat_dataset_v6.csv"


# ============================================================
# V6 TARGETED DATASET
#
# V5 showed two important weaknesses:
#
# 1. Negation:
#    "Nobody threatened me" was sometimes classified as threat.
#
# 2. Short / indirect Hinglish threats:
#    "Unhone bola chup raho warna problem ho sakti hai"
#    was classified as NOT THREAT.
#
# V6 specifically adds examples for these failure modes.
# ============================================================


rows = []


def add(text, label, category, language):
    rows.append({
        "text": text,
        "label": label,
        "category": category,
        "language": language,
        "source": "synthetic_v6"
    })


# ============================================================
# 1. EXPLICIT NEGATION
# ============================================================

not_threat_negation = [

    "Nobody threatened me.",
    "No one has threatened me.",
    "Nobody made any threat against me.",
    "I have not received any threats.",
    "No one has made a threat against my family.",
    "Nobody contacted me to threaten me.",
    "I have not been threatened by anyone.",
    "There has been no threat against me.",
    "No threatening message was sent to me.",
    "Nobody has threatened my family.",
    "I have received no threats about the case.",
    "No one has told me that I would be harmed.",
    "There is no actual threat against me.",
    "Nobody has warned me that I would be harmed.",
    "No one has tried to intimidate me."
]

for text in not_threat_negation:
    add(text, 0, "negation", "english")


# ============================================================
# 2. NEGATION + CASE CONTEXT
# ============================================================

case_negation = [

    "Nobody told me to withdraw the complaint.",
    "No one has asked me to drop the case.",
    "Nobody threatened me about continuing the case.",
    "I was not threatened because of my complaint.",
    "No one has contacted me about the case in a threatening way.",
    "Nobody told me to stop cooperating with the investigation.",
    "I have not received any threats about testifying.",
    "No one has pressured me to change my statement.",
    "Nobody has tried to force me to withdraw the complaint.",
    "I have continued the case without receiving any threats."
]

for text in case_negation:
    add(text, 0, "case_negation", "english")


# ============================================================
# 3. THREATS VS FEAR
# ============================================================

fear_without_threat = [

    "I am afraid that someone might hurt me.",
    "I worry that there could be retaliation.",
    "I am scared about what might happen next.",
    "The case makes me fear for my safety.",
    "I keep imagining that something bad could happen.",
    "I am worried that someone may become angry with me.",
    "I feel unsafe even though nobody has contacted me.",
    "The possibility of retaliation makes me anxious.",
    "I am frightened by the situation but nobody has threatened me.",
    "I am nervous about continuing the case."
]

for text in fear_without_threat:
    add(text, 0, "fear_without_threat", "english")


# ============================================================
# 4. THREATS AGAINST OTHER PEOPLE
# ============================================================

other_person_threats = [

    "I heard that another witness was threatened.",
    "Someone told me another family received threats.",
    "There were threats against another person involved in the case.",
    "I read about a witness being threatened.",
    "Another victim told me that they had received threats.",
    "I heard about threats in the neighbourhood.",
    "Someone else involved in the case was threatened.",
    "The newspaper reported threats against other witnesses.",
    "I know another family was intimidated, but nobody threatened me.",
    "There have been threats against other people involved in similar cases."
]

for text in other_person_threats:
    add(text, 0, "other_person_threat", "english")


# ============================================================
# 5. NON-THREAT ADVICE / SUGGESTIONS
# ============================================================

non_threat_advice = [

    "They advised me not to get involved in the matter.",
    "Someone suggested that I stay away from the dispute.",
    "My friend advised me to avoid the case.",
    "Someone suggested that I forget about the complaint.",
    "They recommended that I speak to a lawyer first.",
    "I was advised to wait before continuing.",
    "Someone told me it might be better to stay out of the matter.",
    "They suggested that I avoid unnecessary conflict.",
    "I was given advice to step away from the dispute.",
    "Someone recommended that I think carefully before continuing."
]

for text in non_threat_advice:
    add(text, 0, "non_threat_advice", "english")


# ============================================================
# 6. INDIRECT / IMPLIED THREATS
# ============================================================

indirect_threats = [

    "He told me to stay quiet or there would be consequences.",
    "They said I should stop talking about the case if I knew what was good for me.",
    "He made it clear that continuing would cause problems for me.",
    "They warned me that my family could suffer if I testified.",
    "He said I would regret going to the police.",
    "They told me to withdraw the complaint unless I wanted trouble.",
    "He reminded me that he knew where my parents lived.",
    "They said things would become difficult if I continued.",
    "He told me that cooperating with the police would be a mistake.",
    "They made it clear that I should not speak in court.",
    "He said I should keep quiet if I wanted things to remain peaceful.",
    "They warned me that there would be consequences if I testified.",
    "He said my job could disappear if I helped the investigation.",
    "They told me that my family would not be safe if I continued.",
    "He suggested that I reconsider my decision unless I wanted problems."
]

for text in indirect_threats:
    add(text, 1, "indirect_threat", "english")


# ============================================================
# 7. SHORT HINGLISH THREATS
# ============================================================

hinglish_threats = [

    "Chup raho warna problem hogi.",
    "Case aage badhaya toh accha nahi hoga.",
    "Police ko bataya toh dekh lena.",
    "Complaint wapas le lo warna problem hogi.",
    "Court mein kuch bola toh consequences honge.",
    "Gawahi di toh tumhare liye accha nahi hoga.",
    "Case continue kiya toh family ko problem hogi.",
    "Police ke paas gaye toh dekh lenge.",
    "Mere khilaaf statement mat dena.",
    "Court mein mere against kuch mat bolna.",
    "Case chhodo warna bahut bura hoga.",
    "Chup raho aur matter khatam karo.",
    "Agar case continue kiya toh tumhe regret hoga.",
    "Family ko involve mat karo warna problem hogi.",
    "Complaint ki toh tumhare liye mushkil ho jayegi."
]

for text in hinglish_threats:
    add(text, 1, "hinglish_threat", "hinglish")


# ============================================================
# 8. HINGLISH FEAR WITHOUT THREAT
# ============================================================

hinglish_non_threat = [

    "Case ko lekar mujhe bahut darr lag raha hai.",
    "Mujhe future ko lekar tension ho rahi hai.",
    "Mujhe lagta hai kuch bura ho sakta hai.",
    "Retaliation ka sochkar mujhe anxiety hoti hai.",
    "Case ki wajah se main bahut nervous hoon.",
    "Mujhe safety ko lekar concern hai.",
    "Kisi ne mujhe dhamki nahi di, bas mujhe darr lag raha hai.",
    "Mere area mein threats ke baare mein suna hai isliye main scared hoon.",
    "Mujhe nahi pata aage kya hoga aur isliye tension hai.",
    "Case continue karne ko lekar main anxious hoon."
]

for text in hinglish_non_threat:
    add(text, 0, "hinglish_fear", "hinglish")


# ============================================================
# 9. HINGLISH NEGATION
# ============================================================

hinglish_negation = [

    "Kisi ne mujhe dhamki nahi di.",
    "Mujhe koi threaten nahi kar raha hai.",
    "Kisi ne complaint wapas lene ko nahi bola.",
    "Mere family ko kisi ne threaten nahi kiya.",
    "Mujhe koi threatening message nahi mila.",
    "Kisi ne mujhe harm karne ki baat nahi boli.",
    "Mujhe case ke wajah se koi dhamki nahi mili.",
    "Kisi ne police ke paas jaane se mujhe nahi roka.",
    "Mere against kisi ne threat nahi diya.",
    "Kisi ne mujhe chup rehne ke liye force nahi kiya."
]

for text in hinglish_negation:
    add(text, 0, "hinglish_negation", "hinglish")


# ============================================================
# 10. HINGLISH INDIRECT THREATS
# ============================================================

hinglish_indirect = [

    "Unhone bola chup raho warna problem ho sakti hai.",
    "Unhone kaha case aage le gaye toh accha nahi hoga.",
    "Police ko bataya toh tumhare liye problem hogi.",
    "Unhone bola complaint wapas le lo warna dekh lena.",
    "Gawahi di toh family ko problem ho jayegi.",
    "Court mein kuch bola toh consequences honge.",
    "Case continue kiya toh job ka problem ho jayega.",
    "Unhone bola zyada bolna mat, warna situation kharab ho sakti hai.",
    "Mujhe bola gaya ki case ko aage mat badhao.",
    "Unhone clear bola ki police ke paas nahi jaana hai.",
    "Agar statement diya toh tumhe regret hoga.",
    "Unhone kaha matter ko yahin khatam karo."
]

for text in hinglish_indirect:
    add(text, 1, "hinglish_indirect", "hinglish")

# ============================================================
# 11. ADDITIONAL TARGETED THREATS
# ============================================================

additional_threats = [

    # Direct threats
    "They said they would hurt me if I reported the incident.",
    "He threatened to harm my brother if I gave evidence.",
    "They told me I would be attacked if I went to the police.",
    "He said my family would suffer if I continued the case.",
    "They threatened to destroy my business if I testified.",

    # Negation contrast, but actual threat
    "They told me to stop the complaint or they would hurt me.",
    "Nobody threatened me at first, but later they warned me to withdraw the case.",
    "I was not threatened when I first complained, but they later threatened my family.",
    "They first advised me to stop, then made it clear there would be consequences.",
    "He initially gave advice, but later threatened me if I continued.",

    # Indirect threats
    "He said I would regret speaking to the authorities.",
    "They told me that cooperating with police would create serious problems.",
    "He made it clear that I should not appear in court.",
    "They said my family might face trouble if I testified.",
    "He warned me that continuing the complaint would not end well.",
    "They told me to think about what could happen to my family.",
    "He said people who speak in court can face consequences.",
    "They made it clear that I should keep silent.",
    "He warned me not to give evidence against them.",
    "They said I should forget the complaint if I wanted peace.",

    # Short coercive statements
    "Withdraw the complaint or you will regret it.",
    "Stay quiet or there will be consequences.",
    "Do not go to the police if you know what is good for you.",
    "Stop the case or your family will suffer.",
    "Do not testify against us.",
    "Keep your mouth shut about the incident.",
    "Do not take this matter to court.",

    # Hinglish threats
    "Police ko bataya toh tumhe problem hogi.",
    "Case band karo warna bahut bura hoga.",
    "Gawahi di toh tumhare family ko dekh lenge.",
    "Complaint ki toh tumhari job chali jayegi.",
    "Court mein bola toh consequences honge.",
    "Case aage badhaya toh tumhe regret hoga.",
    "Police ke paas mat jaana warna problem hogi.",
    "Mere against statement diya toh accha nahi hoga.",
    "Chup raho warna family ko problem hogi.",
    "Complaint wapas lo warna dekh lena.",
    "Case ko yahin khatam karo warna mushkil hogi.",
    "Gawahi mat dena warna tumhare liye accha nahi hoga.",
    "Police ko inform kiya toh tumhe nuksaan ho sakta hai.",
    "Court mein sach mat bolna.",
    "Case continue kiya toh tumhari job ka problem ho jayega.",
    "Matter ko aage le gaye toh consequences honge.",
    "Unhone bola police ke paas gaya toh dekh lenge.",
    "Unhone kaha case chhodo warna problem hogi."
]

for text in additional_threats:
    add(text, 1, "targeted_threat", "english" if not any(
        word in text.lower()
        for word in [
            "ko", "toh", "tumhe", "tumhare", "gawahi",
            "di", "kiya", "kar", "bhi", "unhone",
            "bola", "kaha", "chhodo", "raha", "mat",
            "mein", "jayegi", "hogi", "dena", "gaye"
        ]
    ) else "hinglish")

# ============================================================
# 11. AMBIGUOUS BUT NON-THREAT
# ============================================================

ambiguous_non_threat = [

    "Please think carefully before getting involved.",
    "You should consider whether this case is worth continuing.",
    "Maybe it is better to stay away from the dispute.",
    "I was told to be careful because the situation is complicated.",
    "Someone advised me to speak with a lawyer first.",
    "They said I should avoid unnecessary conflict.",
    "I was asked to wait before making a decision.",
    "Someone suggested that I reconsider my involvement."
]

for text in ambiguous_non_threat:
    add(text, 0, "ambiguous_non_threat", "english")


# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(rows)

# Remove accidental duplicates
df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)

# Shuffle
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save
df.to_csv(OUTPUT_PATH, index=False)


# ============================================================
# SUMMARY
# ============================================================

print("=" * 60)
print("V6 TARGETED THREAT DATASET")
print("=" * 60)

print("\nTotal examples:", len(df))

print("\nLABEL DISTRIBUTION")
print("-" * 30)
print(df["label"].value_counts())

print("\nLANGUAGE DISTRIBUTION")
print("-" * 30)
print(df["language"].value_counts())

print("\nCATEGORY DISTRIBUTION")
print("-" * 30)
print(df["category"].value_counts())

print("\nSAMPLE")
print("-" * 30)

print(
    df[["text", "label", "category", "language"]]
    .head(15)
    .to_string(index=False)
)

print("\n" + "=" * 60)
print("SAVED TO:")
print(OUTPUT_PATH)
print("=" * 60)
