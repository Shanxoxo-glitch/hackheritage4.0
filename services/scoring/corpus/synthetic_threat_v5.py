import random
import pandas as pd

random.seed(42)

OUTPUT_PATH = "training/data/threat_dataset_v5.csv"


# ============================================================
# HELPER
# ============================================================

def add_row(rows, text, label, category, language):
    rows.append({
        "text": text.strip(),
        "label": label,
        "category": category,
        "language": language,
        "source": "synthetic"
    })


# ============================================================
# THREAT DATA
# ============================================================

threat_data = {

    "physical_threat": {

        "english": [
            "They told me I would be hurt if I went to the police.",
            "He warned me that I would regret continuing the case.",
            "They said I would not be safe if I gave my statement.",
            "He told me to stop the complaint or face consequences.",
            "Someone warned me not to take the matter to court.",
            "They said something bad would happen if I kept pursuing the case.",
            "He told me that continuing the case would put me in danger.",
            "They warned me against speaking to the authorities.",
            "I was told to stop cooperating or I would face serious consequences.",
            "They made it clear that I would be in trouble if I continued.",
            "He told me not to speak about the incident unless I wanted problems.",
            "They warned me to think carefully before going to the police.",
            "I was told that things would become dangerous if I continued.",
            "They said I would have to face the consequences if I testified.",
            "He warned me that I would be sorry for taking the case further.",
            "They told me not to make the complaint any bigger.",
            "I was warned that continuing the matter could put me at risk.",
            "They told me that I would pay for continuing with the case.",
            "He made it clear that I should stop pursuing the complaint.",
            "They warned me that I would not be safe if I spoke up.",
        ],

        "hinglish": [
            "Police ke paas gaya toh mere liye achha nahi hoga.",
            "Case continue kiya toh mujhe problem face karni padegi.",
            "Complaint ki toh dekh lena kya hota hai.",
            "Statement diya toh main safe nahi rahunga.",
            "Case aage badhaya toh bahut bura hoga.",
            "Police ko bataya toh consequences face karne padenge.",
            "Complaint continue karne par mujhe nuksan ho sakta hai.",
            "Agar court gaya toh mere liye situation kharab ho jayegi.",
            "Case ko aage mat badhao warna problem hogi.",
            "Gawahi di toh tumhe iska result bhugatna padega.",
        ],
    },


    "family_threat": {

        "english": [
            "They told me my family would suffer if I continued the case.",
            "He warned me to think about my parents before making a complaint.",
            "They said my brother would face problems if I testified.",
            "Someone told me my children would not be safe if I went to court.",
            "They threatened consequences for my family if I refused to withdraw.",
            "He reminded me that he knew where my family lived.",
            "They said my parents could be affected if I spoke to the police.",
            "I was warned that my family would be dragged into the matter.",
            "They told me my family would have problems if I cooperated.",
            "He said I should stop the case for the sake of my family.",
            "They warned me that my relatives could face consequences.",
            "I was told to stay quiet because my family could suffer.",
            "They made it clear that my family could become involved.",
            "He told me that continuing the complaint would create trouble for my parents.",
            "They warned me not to risk my family's safety.",
            "Someone told me that my brother could be targeted.",
            "They said my children could be affected if I continued.",
            "He warned me that my family would pay for my decision.",
            "They told me to withdraw the complaint before my family faced problems.",
            "I was warned that my family would not be left out of the situation.",
        ],

        "hinglish": [
            "Complaint ki toh meri family ko problem hogi.",
            "Case continue kiya toh mere parents ko dekh lenge.",
            "Mere bhai ko bhi consequences face karne padenge.",
            "Case aage badhaya toh family safe nahi rahegi.",
            "Apne family ke baare mein socho aur complaint wapas le lo.",
            "Tumhari wajah se ghar walon ko problem hogi.",
            "Agar statement diya toh mere bachchon ko nuksan ho sakta hai.",
            "Family ko involve nahi karna hai toh case withdraw kar do.",
            "Police ko bataya toh mere parents ko trouble ho sakta hai.",
            "Gawahi di toh tumhare family ko consequences face karne padenge.",
        ],
    },


    "witness_intimidation": {

        "english": [
            "They told me not to appear in court.",
            "He warned me not to give evidence against them.",
            "They asked me to forget what I had seen.",
            "Someone told me not to become involved as a witness.",
            "They said I should reconsider testifying.",
            "He told me not to tell the court what happened.",
            "They warned me against cooperating with the investigation.",
            "I was told to stay away from the courtroom.",
            "They asked me to keep my statement to myself.",
            "He warned me not to speak about what I witnessed.",
            "They told me that testifying would be a bad idea.",
            "Someone pressured me not to provide evidence.",
            "They made it clear that I should not appear as a witness.",
            "He told me to forget everything I had seen.",
            "They warned me before I was supposed to give my statement.",
            "I was told that I should not cooperate with investigators.",
            "They asked me not to discuss the incident in court.",
            "He warned me against supporting the complaint.",
            "They told me to stay out of the case as a witness.",
            "Someone tried to stop me from giving evidence.",
        ],

        "hinglish": [
            "Court mein gawahi mat dena.",
            "Witness mat banna warna problem hogi.",
            "Jo dekha hai woh court mein mat batana.",
            "Gawahi dene se pehle soch lena.",
            "Evidence diya toh consequences honge.",
            "Statement mein jo hua woh mat bolna.",
            "Investigation mein cooperate mat karna.",
            "Court mein testify karne ki zarurat nahi hai.",
            "Witness ke taur par case mein involve mat hona.",
            "Agar gawahi di toh tumhare liye achha nahi hoga.",
        ],
    },


    "case_withdrawal": {

        "english": [
            "They told me to withdraw the complaint.",
            "He asked me to take back my statement.",
            "They pressured me to stop pursuing the case.",
            "Someone told me the complaint should end here.",
            "They warned me to take the matter no further.",
            "He told me to change my statement.",
            "They asked me to forget about the case.",
            "I was pressured into withdrawing the complaint.",
            "They told me to stop cooperating with the case.",
            "He said I should take back what I had reported.",
            "They told me to end the matter before it became worse.",
            "Someone demanded that I withdraw my complaint.",
            "They asked me to stop taking the case forward.",
            "He told me that withdrawing the complaint would be better for me.",
            "They pressured me to change what I had said.",
            "I was told to abandon the complaint.",
            "They warned me not to pursue the case any further.",
            "Someone told me to close the matter and stay quiet.",
            "They demanded that I stop with the complaint.",
            "He told me to withdraw everything I had reported.",
        ],

        "hinglish": [
            "Complaint wapas le lo.",
            "Case ko aage mat badhao.",
            "Statement change kar do.",
            "Complaint withdraw karna hi better hoga.",
            "Case yahin khatam kar do.",
            "Apni complaint wapas le lo warna problem hogi.",
            "Matter ko aur aage mat le jao.",
            "Statement wapas lena padega.",
            "Case continue karne ki zarurat nahi hai.",
            "Agar safe rehna hai toh complaint withdraw kar do.",
        ],
    },


    "financial_coercion": {

        "english": [
            "They told me I could lose my job if I reported this.",
            "He warned me that my employment would be affected.",
            "They said my salary could stop if I cooperated.",
            "Someone told me that my income was at risk.",
            "They warned me not to jeopardize my livelihood by speaking up.",
            "He said I could lose my position if I testified.",
            "They told me my job would not be safe if I continued.",
            "I was warned that cooperating could affect my employment.",
            "They said my source of income could disappear.",
            "He pressured me to stay quiet to protect my job.",
            "They warned me that my salary could be affected.",
            "Someone told me not to risk my employment over the case.",
            "They said continuing the complaint could cost me my livelihood.",
            "I was told that my financial situation would suffer if I cooperated.",
            "He warned me that my job was in their hands.",
            "They told me to stop cooperating if I wanted to keep working.",
            "Someone pressured me by threatening my income.",
            "They said I would have employment problems if I testified.",
            "He told me that speaking up could cost me my job.",
            "They warned me that continuing the case could affect my livelihood.",
        ],

        "hinglish": [
            "Complaint ki toh job chali jayegi.",
            "Case mein cooperate kiya toh salary band ho jayegi.",
            "Gawahi di toh job safe nahi rahegi.",
            "Case continue kiya toh income ka problem hoga.",
            "Authorities se baat ki toh job lose kar doge.",
            "Complaint withdraw nahi ki toh job se nikalwa denge.",
            "Case continue kiya toh earning affect hogi.",
            "Statement diya toh employment ka issue ho jayega.",
            "Apni job risk mein mat daalo aur complaint wapas le lo.",
            "Cooperate kiya toh salary ka problem ho sakta hai.",
        ],
    },


    "forced_silence": {

        "english": [
            "They told me not to tell anyone what happened.",
            "He warned me to keep quiet about the incident.",
            "They asked me to stop talking about the case.",
            "Someone told me not to speak to the police.",
            "They told me that nobody should hear about the incident.",
            "He pressured me to stay silent.",
            "They warned me against discussing the complaint.",
            "I was told to keep the matter to myself.",
            "They asked me not to tell the authorities.",
            "He told me to stop speaking about what I had seen.",
            "They warned me not to discuss the case with anyone.",
            "Someone told me to stay quiet about the investigation.",
            "They pressured me into keeping silent.",
            "He said I should never mention the incident again.",
            "They told me to remain silent about what happened.",
            "I was warned not to talk about the complaint.",
            "They asked me to stop telling people about the case.",
            "Someone told me that I should keep my mouth shut.",
            "They warned me not to discuss the matter publicly.",
            "He told me to stay quiet if I wanted things to remain peaceful.",
        ],

        "hinglish": [
            "Kisi ko kuch mat batana.",
            "Is incident ke baare mein chup raho.",
            "Police ko kuch mat bolna.",
            "Case ke baare mein kisi se baat mat karna.",
            "Jo hua woh kisi ko mat batana.",
            "Complaint ke baare mein silent raho.",
            "Court mein iske baare mein kuch mat bolna.",
            "Kisi ko bataya toh problem hogi.",
            "Case ko lekar chup rehna.",
            "Authorities ko kuch nahi batana.",
        ],
    },
}


# ============================================================
# NON-THREAT DATA
# ============================================================

non_threat_data = {

    "fear": {

        "english": [
            "I am scared about what might happen next.",
            "I am worried about the future of my case.",
            "I feel nervous whenever I think about the hearing.",
            "I am afraid of what will happen in court.",
            "The uncertainty is making me anxious.",
            "I keep worrying about the situation.",
            "I feel frightened by everything that has happened.",
            "I am nervous because I do not know what to expect.",
            "The case is making me very anxious.",
            "I am worried about how everything will turn out.",
            "I feel uneasy about going to court.",
            "I am scared because the process is unfamiliar to me.",
            "Thinking about the case makes me anxious.",
            "I am worried about what comes next.",
            "I feel nervous about speaking during the hearing.",
        ],

        "hinglish": [
            "Mujhe aage kya hoga iska darr lag raha hai.",
            "Case ko lekar bahut anxiety ho rahi hai.",
            "Hearing ke baare mein soch kar nervous ho jata hoon.",
            "Mujhe future ko lekar bahut tension hai.",
            "Puri situation se darr lag raha hai.",
            "Mujhe court jaane mein anxiety ho rahi hai.",
            "Samajh nahi aa raha aage kya hoga.",
            "Case ki wajah se bahut nervous feel kar raha hoon.",
            "Mujhe situation ko lekar fear ho raha hai.",
            "Uncertainty ki wajah se anxiety ho rahi hai.",
        ],
    },


    "legal_stress": {

        "english": [
            "I do not understand the legal process.",
            "The paperwork is overwhelming me.",
            "I am nervous about giving my statement.",
            "I have never dealt with a case before.",
            "The hearing process is confusing.",
            "I am worried that I will make a mistake in court.",
            "I do not know what to expect during the hearing.",
            "The legal process is making me stressed.",
            "I am having trouble understanding the paperwork.",
            "I feel overwhelmed by the court procedure.",
            "I am unsure about what I should do during the hearing.",
            "The case procedure is difficult for me to understand.",
            "I feel stressed whenever I have to deal with the paperwork.",
            "I am worried about saying something incorrectly in court.",
            "I find the legal process emotionally exhausting.",
        ],

        "hinglish": [
            "Mujhe legal process samajh nahi aa raha.",
            "Court procedure ko lekar stress hai.",
            "Statement dene ko lekar nervous hoon.",
            "Mujhe hearing ka process confusing lag raha hai.",
            "Paperwork handle karna difficult lag raha hai.",
            "Court mein kya hoga samajh nahi aa raha.",
            "Legal case ka experience nahi hai isliye tension ho rahi hai.",
            "Mujhe apni statement ko lekar concern hai.",
            "Hearing ke liye prepare karna stressful lag raha hai.",
            "Legal process bahut overwhelming hai.",
        ],
    },


    "sadness": {

        "english": [
            "I have been feeling very sad since the incident.",
            "I feel emotionally exhausted.",
            "I have been crying a lot lately.",
            "Everything has become emotionally difficult for me.",
            "I feel lonely after everything that happened.",
            "I do not feel like talking to anyone.",
            "I feel drained by the situation.",
            "I am struggling emotionally.",
            "I have been feeling low for several days.",
            "This experience has left me feeling very upset.",
            "I feel emotionally tired after dealing with everything.",
            "I have been finding it hard to feel normal again.",
            "The situation has affected me emotionally.",
            "I feel down whenever I think about what happened.",
            "I have been having a difficult time emotionally.",
        ],

        "hinglish": [
            "Is incident ke baad main bahut sad hoon.",
            "Mujhe bahut lonely feel ho raha hai.",
            "Main emotionally exhausted ho gaya hoon.",
            "Mera mood bahut low chal raha hai.",
            "Mujhe kisi se baat karne ka mann nahi karta.",
            "Situation ki wajah se emotionally drained hoon.",
            "Main kaafi upset feel kar raha hoon.",
            "Pichhle kuch din se bahut low feel ho raha hai.",
            "Sab kuch emotionally difficult lag raha hai.",
            "Mujhe bahut akela feel ho raha hai.",
        ],
    },


    "hopelessness": {

        "english": [
            "I do not know how I will handle this situation.",
            "Everything feels impossible right now.",
            "I feel like nothing is getting better.",
            "I do not know where to turn for help.",
            "I feel completely overwhelmed.",
            "I do not know what I am supposed to do next.",
            "The situation feels too difficult to manage.",
            "I feel helpless about what is happening.",
            "I cannot see a clear way forward.",
            "I feel lost because everything is so complicated.",
            "I do not know how to get through this.",
            "It feels like I have no idea what to do next.",
            "I am struggling to see a solution.",
            "Everything feels too difficult at the moment.",
            "I feel unable to cope with everything happening around me.",
        ],

        "hinglish": [
            "Mujhe samajh nahi aa raha kya karun.",
            "Lag raha hai kuch bhi theek nahi hoga.",
            "Mujhe situation bahut difficult lag rahi hai.",
            "Samajh nahi aa raha kis se help loon.",
            "Main bahut helpless feel kar raha hoon.",
            "Aage ka koi clear way nahi dikh raha.",
            "Puri situation handle karna mushkil lag raha hai.",
            "Mujhe lag raha hai main sab kuch manage nahi kar paunga.",
            "Main is situation mein lost feel kar raha hoon.",
            "Kuch samajh nahi aa raha kaise aage badhun.",
        ],
    },


    "anger": {

        "english": [
            "I am extremely angry about what happened.",
            "I am frustrated with how slowly the case is moving.",
            "I am upset about how my complaint was handled.",
            "I feel angry because nobody is listening to me.",
            "The situation has made me very frustrated.",
            "I am angry about the way I was treated.",
            "I feel irritated whenever I think about the case.",
            "I am frustrated that nothing seems to be changing.",
            "I feel angry and exhausted by the process.",
            "I am upset about how complicated everything has become.",
            "I am frustrated with the lack of response.",
            "I feel angry whenever I think about what happened.",
            "The slow process is making me increasingly frustrated.",
            "I am upset that nobody seems to understand my situation.",
            "I feel irritated by how difficult the process has become.",
        ],

        "hinglish": [
            "Jo hua usko lekar mujhe bahut gussa hai.",
            "Complaint ka response nahi milne se frustration hai.",
            "Case slow chalne ki wajah se irritate hoon.",
            "Mujhe situation par bahut gussa aa raha hai.",
            "Koi meri baat nahi sun raha isliye frustrated hoon.",
            "Process ki wajah se bahut irritation ho rahi hai.",
            "Mujhe complaint handle karne ka tareeka pasand nahi aaya.",
            "Case ki wajah se mentally frustrated hoon.",
            "Mujhe pura situation unfair lag raha hai.",
            "Main is process se bahut upset hoon.",
        ],
    },


    "general_distress": {

        "english": [
            "The whole situation has been difficult for me.",
            "I am having trouble concentrating because of the case.",
            "I have not been able to sleep properly because I keep thinking about it.",
            "The situation has affected my daily routine.",
            "I feel stressed whenever the case comes up.",
            "I am finding it difficult to focus on normal things.",
            "This situation has been emotionally exhausting.",
            "I keep worrying about the case throughout the day.",
            "I feel unsettled because of everything that happened.",
            "The case has made normal activities harder for me.",
            "I am struggling to keep up with my normal routine.",
            "It has become difficult for me to focus on college.",
            "I keep thinking about the situation when I should be working.",
            "The case has been affecting my ability to concentrate.",
            "I feel mentally tired whenever I think about everything.",
        ],

        "hinglish": [
            "Puri situation ki wajah se bahut stress hai.",
            "Case ki wajah se focus karna mushkil ho raha hai.",
            "Incident ke baad routine disturb ho gaya hai.",
            "Mujhe normal cheezon par concentrate karna difficult lag raha hai.",
            "Case ke baare mein din bhar sochta rehta hoon.",
            "Situation ki wajah se mentally tired hoon.",
            "Sab kuch bahut stressful lag raha hai.",
            "Incident ke baad se main unsettled feel kar raha hoon.",
            "Case ki wajah se daily life affect ho rahi hai.",
            "Mujhe situation se kaafi emotional stress ho raha hai.",
        ],
    },
}


# ============================================================
# HARD NEGATIVES
# ============================================================

hard_negatives = [

    # English
    "I am scared that they might hurt me, but nobody has threatened me.",
    "I am worried they could retaliate even though nobody has contacted me.",
    "The possibility of retaliation is making me extremely anxious.",
    "I am afraid something bad might happen to my family.",
    "Nobody has threatened me, but I am worried about what could happen.",
    "I heard about threats against other people and it made me nervous.",
    "I am worried that someone might threaten me in the future.",
    "The thought of being threatened makes me anxious.",
    "I am frightened by the possibility that things could get worse.",
    "I am concerned about my safety even though nobody has intimidated me.",
    "Someone mentioned threats during the hearing and I became nervous.",
    "I keep thinking about possible retaliation.",
    "I am afraid of being threatened even though nothing has happened.",
    "I worry about what they might do, but they have not said anything to me.",
    "The word threat came up in the discussion and it made me uncomfortable.",

    # Hinglish
    "Mujhe darr hai ki woh mujhe hurt kar sakte hain, lekin kisi ne dhamki nahi di.",
    "Mujhe retaliation ka fear hai, lekin mujhe koi threat nahi mila.",
    "Mujhe darr hai ki mere family ko kuch ho sakta hai.",
    "Kisi ne mujhe threaten nahi kiya, bas mujhe future ko lekar concern hai.",
    "Threats ke baare mein sun kar mujhe anxiety ho rahi hai.",
    "Mujhe lagta hai future mein threat ho sakta hai, lekin abhi kuch nahi hua.",
    "Kisi aur ko threat mila tha aur uske baad mujhe darr lagne laga.",
    "Mujhe safety ko lekar concern hai, kisi ne mujhe directly threaten nahi kiya.",
]


# ============================================================
# BUILD DATASET
# ============================================================

rows = []


# ------------------------------------------------------------
# Add exactly 50 examples from every threat category
# ------------------------------------------------------------

for category, languages in threat_data.items():

    for language, examples in languages.items():

        selected = examples[:]

        random.shuffle(selected)

        # 40 English + 10 Hinglish
        if language == "english":
            selected = selected[:40]
        else:
            selected = selected[:10]

        for text in selected:
            add_row(
                rows,
                text,
                1,
                category,
                language
            )


# ------------------------------------------------------------
# Add exactly 50 examples from every non-threat category
# ------------------------------------------------------------

for category, languages in non_threat_data.items():

    for language, examples in languages.items():

        selected = examples[:]

        random.shuffle(selected)

        if language == "english":
            selected = selected[:40]
        else:
            selected = selected[:10]

        for text in selected:
            add_row(
                rows,
                text,
                0,
                category,
                language
            )


# ------------------------------------------------------------
# Add hard negatives
# ------------------------------------------------------------

for text in hard_negatives:

    language = "hinglish" if text.startswith("Mujhe") or text.startswith("Kisi") else "english"

    add_row(
        rows,
        text,
        0,
        "hard_negative",
        language
    )


# ============================================================
# CLEAN
# ============================================================

df = pd.DataFrame(rows)

df = df.drop_duplicates(
    subset=["text"]
)

df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print("=" * 60)
print("THREAT DATASET V5 GENERATED")
print("=" * 60)

print()
print("Total examples:", len(df))

print()
print("Label counts:")
print(df["label"].value_counts())

print()
print("Category counts:")
print(df["category"].value_counts())

print()
print("Language counts:")
print(df["language"].value_counts())

print()
print("Source counts:")
print(df["source"].value_counts())

print()
print("Sample examples:")
print(
    df.sample(
        min(30, len(df)),
        random_state=42
    ).to_string(index=False)
)

print()
print("=" * 60)
print("Saved to:", OUTPUT_PATH)
print("=" * 60)