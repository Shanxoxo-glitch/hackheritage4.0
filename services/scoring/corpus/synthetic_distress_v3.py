"""
DISTRESS DATASET V3
===================

Labels (prototype perception signal, NOT a clinical scale):
  0 = LOW      : neutral/factual, coping, normal functioning, mild manageable stress
  1 = MODERATE : explicit worry/nervousness/stress, some functional impact
                 (a little less sleep, harder to focus, irritable) but still coping
  2 = HIGH     : overwhelming fear/hopelessness/panic, major functional collapse
                 (cannot sleep/eat/work/leave the house), crisis language

Why V3 exists
-------------
V2 (120 examples) was too small: MuRIL never left the uniform-prediction
plateau (loss stuck at ln(3) = 1.0986). V3 fixes the data side:

  * ~90 HANDWRITTEN natural sentences per class (English + Hinglish)
  * ~70 TEMPLATED sentences per class built from fragments, each tagged with
    a `group` id (its core phrase) so the splitter can keep whole groups out
    of validation -> no paraphrase leakage (lesson learned from threat V3).
  * The TEST split is handwritten-only. Templated text never reaches test.

Columns: id, text, label, label_name, language, source, group
"""

import random
import pandas as pd

SEED = 42
OUTPUT_PATH = "training/data/distress_dataset_v3.csv"
TEMPLATED_PER_CELL = 35          # per (label, language)

LABEL_NAMES = {0: "LOW", 1: "MODERATE", 2: "HIGH"}


# ============================================================
# HANDWRITTEN SENTENCES
# ============================================================

HANDWRITTEN = {

    0: {
        "english": [
            "The hearing is on the 14th, and I have my documents ready.",
            "My lawyer explained the process and it makes sense to me.",
            "Things are fine at home, and work is going as usual.",
            "I went to the police station today and filed the papers without any trouble.",
            "I'm managing the case alongside my job and it's okay.",
            "I feel calm about the next hearing.",
            "Nothing new has happened this week, everything is normal.",
            "I slept well and had a normal day.",
            "The counsellor called to check in and I told her I'm doing alright.",
            "I'm a bit busy with the paperwork but it's not a problem.",
            "I understand the next steps and I'm not worried.",
            "My family has been supportive and I feel steady.",
            "The compensation form was submitted and I'm just waiting now.",
            "I was nervous last month, but now I feel much better.",
            "The case is moving slowly, which is expected, and I'm fine with it.",
            "I attended the hearing and it went as planned.",
            "I'm eating and sleeping normally.",
            "Work is keeping me occupied and I feel alright.",
            "I just wanted to confirm the date of the next hearing.",
            "Everything is under control on my side.",
            "I'm not stressed about the case right now.",
            "I have a copy of the FIR and all my receipts in one folder.",
            "I've been going to the fields every day like before.",
            "My brother is coming with me to the court, so I feel comfortable.",
            "The officer was polite and explained everything clearly.",
            "Honestly, I don't think about the case much these days.",
            "I'm okay. Just checking in as scheduled.",
            "Today was a good day, I met my friends in the evening.",
            "I feel confident about giving my statement.",
            "There's nothing to report, things are quiet.",
            "The paperwork is tedious but I'm handling it.",
            "I got the notice and I know what to do next.",
            "My mind is at ease after talking to the lawyer.",
            "I feel safe at home and my routine is normal.",
            "Nothing is bothering me at the moment.",
            "I'm sleeping fine and going to work regularly.",
            "The delay is annoying, but it doesn't affect my day.",
            "I'm focused on my children's school work this week.",
            "I've been feeling relaxed since the last hearing.",
            "I'm fine, thank you for checking.",
            "The weather has been nice and I've been keeping busy.",
            "I have no complaints about how the case is going.",
            "I know the hearing is in two weeks and I've planned my leave.",
            "My health is good and my mood is normal.",
            "I don't feel any pressure about the case at present.",
            "Things have settled down and I feel at peace.",
            "I finished my work early today and rested.",
            "I understand the process may take time and I'm patient.",
            "I feel supported by the counsellor and the lawyer.",
            "Life is going on as usual.",
            "I'm not afraid of attending court.",
            "I was able to concentrate on my work all week.",
            "I have started sleeping properly again.",
            "The next step is the witness statement, and I'm prepared.",
            "Everything is alright at my end.",
        ],
        "hinglish": [
            "Sab theek hai, koi problem nahi.",
            "Hearing 14 tarikh ko hai, papers ready hain.",
            "Lawyer ne sab samjha diya, ab clear hai.",
            "Kaam normal chal raha hai, ghar pe bhi sab theek.",
            "Aaj thana gaya tha, kaagaz jama ho gaye, koi dikkat nahi hui.",
            "Main case ko lekar tension mein nahi hoon.",
            "Neend theek aa rahi hai, khana bhi theek.",
            "Bas next date confirm karni thi.",
            "Pichle mahine ghabrahat thi, ab kaafi behtar hoon.",
            "Case slow chal raha hai par mujhe koi jaldi nahi.",
            "Ghar wale saath hain, main theek hoon.",
            "Court jaane mein koi darr nahi lagta.",
            "Aaj ka din accha tha, shaam ko doston se mila.",
            "Compensation form bhar diya, ab wait hai.",
            "Sab control mein hai mere taraf se.",
            "Case ke baare mein zyada sochta nahi ab.",
            "Officer ne achhe se samjhaya, koi issue nahi.",
            "Roz khet jaa raha hoon pehle jaisa.",
            "Bhai mere saath court aayega, toh comfortable hoon.",
            "Kuch naya nahi hua is hafte, sab normal.",
            "Main theek hoon, bas check-in kar raha tha.",
            "Statement dene ko lekar confident hoon.",
            "Paperwork boring hai par manage ho raha hai.",
            "Notice mil gaya, aage kya karna hai pata hai.",
            "Ghar pe safe feel karta hoon, routine normal hai.",
            "Abhi koi cheez pareshan nahi kar rahi.",
            "Kaam pe regular jaa raha hoon.",
            "Delay se thoda irritation hai par din pe asar nahi.",
            "Bachon ki padhai pe dhyan de raha hoon is hafte.",
            "Last hearing ke baad se relaxed hoon.",
            "Sehat theek hai, mood bhi normal.",
            "Case ko lekar abhi koi pressure nahi hai.",
            "Sab settle ho gaya hai, shanti hai.",
            "Lawyer aur counsellor ka support hai, theek lag raha hai.",
            "Zindagi normal chal rahi hai.",
        ],
    },

    1: {
        "english": [
            "I keep thinking about the hearing and it's hard to relax.",
            "I'm a little anxious about giving my statement next week.",
            "I've been sleeping a bit less since the notice came.",
            "The case is on my mind a lot, but I'm still going to work.",
            "I feel nervous whenever the lawyer calls.",
            "I'm worried about how the hearing will go.",
            "It's been hard to concentrate at work this week.",
            "I'm managing, but the stress is getting to me some days.",
            "I get tense every time I have to go to the police station.",
            "The delay is frustrating and it's starting to bother me.",
            "I feel uneasy about seeing the other party in court.",
            "My appetite has been a bit off lately.",
            "I'm coping, but I'd feel better if the case moved faster.",
            "Some nights I lie awake thinking about what will happen.",
            "I've been more irritable than usual with my family.",
            "I'm worried about the cost of travelling to court again.",
            "I feel a knot in my stomach when I think about the hearing.",
            "It's stressful, but I'm trying to stay positive.",
            "I've been feeling low since the last hearing was postponed.",
            "I'm not sleeping as well as I used to.",
            "I worry that I'll forget details when I testify.",
            "I feel restless most evenings.",
            "The pressure of the case is starting to affect my mood.",
            "I'm handling it, but I feel drained after each court visit.",
            "I've been skipping meals because I'm preoccupied with the case.",
            "My mind keeps drifting to the case during work.",
            "I feel a bit scared about the next step, but I'll go.",
            "I'm tired of waiting and it's making me anxious.",
            "I get a headache when I think about the paperwork.",
            "I haven't been myself lately because of this case.",
            "I'm okay most of the time, but some days are hard.",
            "I feel uncertain and it's difficult to plan anything.",
            "I've been worried about what people in the village are saying.",
            "Honestly, the case is weighing on me more than I expected.",
            "I feel on edge before every phone call about the case.",
            "I'm somewhat stressed but I'm still able to manage my routine.",
            "I need some reassurance, I've been feeling shaky about all this.",
            "I think about the incident sometimes and it makes me sad.",
            "I worry about my family's reaction to the hearing.",
            "Concentrating on anything has been harder this month.",
            "I've started avoiding conversations about the case because they stress me out.",
            "I feel anxious but I know I have support.",
            "I'm not sure I'm ready for the cross-examination.",
            "My sleep is disturbed a couple of nights a week.",
            "The uncertainty is getting on my nerves.",
            "I'm doing my work, but I feel distracted and tense.",
            "Some days I feel like giving up on the case, but then I carry on.",
            "I felt shaky after the last hearing, but I'm slowly settling.",
            "I'm worried about money because I've missed work for court dates.",
            "I keep replaying the incident in my head at night.",
            "I've been feeling nervous and it's affecting my appetite a little.",
            "I'm coping but I'd like to talk to the counsellor soon.",
            "The waiting makes me anxious, especially before each date.",
            "I'm more stressed than last month, but I'm still functioning.",
            "I feel worried, though I can still get through my day.",
        ],
        "hinglish": [
            "Hearing ke baare mein sochta rehta hoon, relax nahi ho pa raha.",
            "Statement dene ko lekar thoda anxious hoon.",
            "Notice aane ke baad se neend thodi kam ho gayi hai.",
            "Case dimaag mein rehta hai, par kaam pe jaa raha hoon.",
            "Lawyer ka phone aata hai toh nervous ho jaata hoon.",
            "Hearing kaise jayegi, iski chinta hai.",
            "Is hafte kaam pe dhyan lagana mushkil raha.",
            "Manage kar raha hoon par kabhi kabhi stress zyada ho jaata hai.",
            "Thane jaane se pehle tension ho jaati hai.",
            "Delay se frustration ho rahi hai, ab pareshan karne laga hai.",
            "Court mein unko dekhne ka sochke uneasy lagta hai.",
            "Bhookh thodi kam ho gayi hai aajkal.",
            "Raat ko kabhi kabhi jaagta rehta hoon ki kya hoga.",
            "Ghar walon pe zyada chidh raha hoon aajkal.",
            "Court jaane ka kharcha sochke chinta hoti hai.",
            "Hearing ka sochke pet mein ajeeb sa lagta hai.",
            "Stress hai par positive rehne ki koshish kar raha hoon.",
            "Date postpone hone ke baad se mood low hai.",
            "Pehle jaisi neend nahi aa rahi.",
            "Darr hai ki gawahi dete waqt details bhool jaunga.",
            "Shaam ko bechaini si rehti hai.",
            "Har court visit ke baad thak jaata hoon.",
            "Case ki wajah se kaam mein dhyan bhatak jaata hai.",
            "Agle step se thoda darr lagta hai par jaunga.",
            "Wait karte karte thak gaya hoon, anxiety hoti hai.",
            "Paperwork ka sochke sar dard hone lagta hai.",
            "Zyadatar theek hoon, par kuch din mushkil hote hain.",
            "Gaon mein log kya bol rahe hain, uski chinta hai.",
            "Case ka bojh umeed se zyada lag raha hai.",
            "Case ke phone se pehle ghabrahat hoti hai.",
            "Thoda stress hai par routine chal raha hai.",
            "Cross-examination ke liye ready hoon ya nahi, pata nahi.",
            "Hafte mein do-teen raat neend kharab hoti hai.",
            "Court ki dates ki wajah se kaam chhoota, paison ki chinta hai.",
            "Raat ko incident baar baar yaad aata hai.",
        ],
    },

    2: {
        "english": [
            "I can't sleep at all, I lie awake every night shaking.",
            "I feel like I can't go on with this anymore.",
            "I'm terrified to leave the house.",
            "I haven't eaten properly in days, I can't stop crying.",
            "My heart races every time I hear a vehicle outside.",
            "I feel completely hopeless about everything.",
            "I'm having panic attacks almost every day.",
            "I can't work, I can't think, I can't do anything.",
            "I feel like my life is falling apart.",
            "I'm so scared I've stopped sending my children to school.",
            "I wish this would all just end, I can't take it.",
            "Everything feels dark and I don't see a way out.",
            "I'm shaking as I write this, I'm so afraid.",
            "I can't face the hearing, I feel like collapsing.",
            "I feel numb and empty all the time.",
            "I haven't slept in three nights because of the fear.",
            "I feel like nobody can help me and I'm all alone.",
            "I keep having nightmares about the incident every night.",
            "I'm too frightened to go to the village well anymore.",
            "I feel like I'm losing my mind.",
            "I've stopped eating, I feel sick all the time.",
            "I burst into tears at work and had to go home.",
            "I feel worthless and I don't want to see anyone.",
            "The fear is unbearable, I can't breathe properly.",
            "I'm exhausted, I can't cope with any of this anymore.",
            "I don't feel safe anywhere, not even at home.",
            "Every day is worse than the last and I'm breaking down.",
            "I've lost all hope that things will ever get better.",
            "I can't stop shaking and my chest hurts from the anxiety.",
            "I'm so overwhelmed I can't even get out of bed.",
            "I feel like I'm drowning and no one is coming.",
            "I'm afraid something terrible is going to happen to my family.",
            "I have no energy, no appetite, and no will to continue.",
            "I can't stop the panic, it comes over me without warning.",
            "I feel like giving up on everything, including myself.",
            "I'm crying all the time and I can't control it.",
            "My hands tremble so badly I can't hold a cup.",
            "I've isolated myself completely, I can't face people.",
            "The pressure is crushing me and I feel I might break.",
            "I'm in constant dread from morning until night.",
            "I can't remember the last time I felt okay.",
            "My body hurts from the stress and I can't function.",
            "I'm scared to sleep because of the nightmares.",
            "I feel there is no point in anything anymore.",
            "I'm at my breaking point and I have no one to turn to.",
            "I feel so much fear that I've stopped going to work entirely.",
            "I keep thinking something awful will happen at the hearing.",
            "I've been vomiting from anxiety before every court date.",
            "I feel trapped and completely helpless.",
            "I don't know how much longer I can bear this.",
            "I can't concentrate on anything, my mind is in pieces.",
            "I'm having a breakdown, I need help right now.",
            "My whole body is tense, I can't eat or sleep or rest.",
            "I've been thinking that my family would be better off without me.",
            "Please help me, I don't know what to do anymore.",
        ],
        "hinglish": [
            "Raat bhar neend nahi aati, kaanpta rehta hoon.",
            "Ab aur nahi ho raha mujhse, main toot gaya hoon.",
            "Ghar se bahar nikalne mein bahut darr lagta hai.",
            "Kai din se theek se khaya nahi, rona band nahi hota.",
            "Bahar gaadi ki awaaz aate hi dil zor se dhadakne lagta hai.",
            "Sab kuch hopeless lag raha hai.",
            "Roz panic attack jaisa ho raha hai.",
            "Na kaam ho raha hai, na kuch sochne ki himmat.",
            "Lagta hai zindagi bikhar rahi hai.",
            "Itna darr hai ki bachon ko school bhejna band kar diya.",
            "Bas sab khatam ho jaye, ab bardasht nahi hota.",
            "Sab andhera lagta hai, koi raasta nahi dikhta.",
            "Likhte likhte haath kaanp rahe hain, itna darr hai.",
            "Hearing ka saamna nahi kar sakta, lagta hai gir jaunga.",
            "Andar se bilkul khaali aur sunn ho gaya hoon.",
            "Teen raat se neend nahi aayi darr ke maare.",
            "Koi meri madad nahi kar sakta, main bilkul akela hoon.",
            "Roz raat incident ke bure sapne aate hain.",
            "Kuen tak jaane mein bhi ab bahut darr lagta hai.",
            "Lagta hai dimaag kharab ho jayega.",
            "Khana chhod diya, har waqt jee machalta hai.",
            "Kaam pe rona aa gaya, ghar aana pada.",
            "Khud ko bekaar samajhta hoon, kisi se milna nahi chahta.",
            "Darr itna hai ki saans theek se nahi aati.",
            "Bilkul thak gaya hoon, ab kuch sambhal nahi raha.",
            "Kahin bhi safe nahi lagta, ghar mein bhi nahi.",
            "Har din pehle se bura hai, main bikhar raha hoon.",
            "Ummeed bilkul khatam ho gayi hai.",
            "Bed se uthne ki bhi himmat nahi hoti, itna bojh hai.",
            "Lagta hai doob raha hoon aur koi bachane nahi aayega.",
            "Darr hai ki parivaar ke saath kuch bahut bura ho jayega.",
            "Na taakat hai, na bhookh, na jeene ki ichha.",
            "Har waqt rona aata hai, control nahi hota.",
            "Sochta hoon ki mere bina ghar walon ko behtar hoga.",
            "Please meri madad karo, ab kuch samajh nahi aa raha.",
        ],
    },
}


# ============================================================
# TEMPLATE FRAGMENTS
# ============================================================
# Each templated sentence gets group = tpl_{lang}_{label}_{core index}
# where "core" is the fragment that carries the class meaning.

LOW_OPENERS = {
    "english": ["", "Just checking in:", "Update from my side:", "This week,",
                "Since the last call,", "As of today,"],
    "hinglish": ["", "Bas update de raha hoon:", "Is hafte", "Pichli baat ke baad se",
                 "Aaj tak"],
}
LOW_STATES = {
    "english": [
        "things are normal", "I'm doing fine", "work and home are both okay",
        "I'm sleeping and eating well", "nothing has changed",
        "I feel calm about the case", "I'm managing the case without any trouble",
        "my routine is the same as usual",
    ],
    "hinglish": [
        "sab theek hai", "main theek hoon", "kaam aur ghar dono theek hain",
        "neend aur khana dono theek hai", "kuch badla nahi hai",
        "case ko lekar main shaant hoon", "case bina dikkat ke manage ho raha hai",
        "routine pehle jaisa hi hai",
    ],
}

MOD_CONTEXTS = {
    "english": ["Since the notice came", "Before the hearing", "After the last court visit",
                "With the date coming up", "Because of the delay", "This month"],
    "hinglish": ["Notice aane ke baad se", "Hearing se pehle", "Last court visit ke baad",
                 "Date paas aa rahi hai toh", "Delay ki wajah se", "Is mahine"],
}
MOD_FEELINGS = {
    "english": [
        "I've been worried", "I feel nervous", "I've been sleeping a little less",
        "it's been hard to focus", "I feel tense", "I've been feeling low",
        "I'm a bit anxious", "I feel uneasy",
    ],
    "hinglish": [
        "chinta ho rahi hai", "nervous lag raha hai", "neend thodi kam ho gayi hai",
        "focus karna mushkil hai", "tension rehti hai", "mood low rehta hai",
        "thodi ghabrahat hai", "bechaini rehti hai",
    ],
}
MOD_COPING = {
    "english": ["but I'm still going to work", "but I'm managing",
                "though I can get through the day", "but I'm coping",
                "but my routine is mostly okay", ""],
    "hinglish": ["par kaam pe jaa raha hoon", "par manage ho raha hai",
                 "phir bhi din nikal jaata hai", "par sambhal raha hoon",
                 "par routine theek hai", ""],
}

HIGH_STATES = {
    "english": [
        "I can't sleep at all", "I'm terrified all the time", "I can't stop crying",
        "I feel completely hopeless", "I'm having panic attacks",
        "I can't eat or sleep", "I feel like I'm breaking down",
        "I don't feel safe anywhere", "I can't stop shaking", "I feel like giving up",
    ],
    "hinglish": [
        "Bilkul neend nahi aati", "Har waqt darr lagta hai", "Rona band nahi hota",
        "Sab hopeless lagta hai", "Panic attack jaise hote hain",
        "Na kha pa raha hoon na so pa raha hoon", "Lagta hai toot raha hoon",
        "Kahin safe nahi lagta", "Kaanpna band nahi hota", "Sab chhod dene ka man karta hai",
    ],
}
HIGH_IMPACTS = {
    "english": [
        "and I can't go to work", "and I can't take care of my children",
        "and I can't face anyone", "and nothing helps",
        "and I don't know what to do", "and I feel I can't go on", "",
    ],
    "hinglish": [
        "aur kaam pe nahi jaa pa raha", "aur bachon ka dhyan nahi rakh pa raha",
        "aur kisi ka saamna nahi kar sakta", "aur kuch kaam nahi aa raha",
        "aur samajh nahi aata kya karun", "aur lagta hai ab aur nahi", "",
    ],
}


def _cap(s):
    return s[0].upper() + s[1:] if s else s


def build_templated(label, lang):
    """Return list of (text, group) for one (label, language) cell."""
    out = []
    if label == 0:
        for ci, state in enumerate(LOW_STATES[lang]):
            for opener in LOW_OPENERS[lang]:
                text = (opener + " " + state).strip() if opener else _cap(state)
                out.append((text + ".", f"tpl_{lang}_0_{ci}"))
    elif label == 1:
        for ci, feel in enumerate(MOD_FEELINGS[lang]):
            for ctx in MOD_CONTEXTS[lang]:
                for cope in MOD_COPING[lang]:
                    text = f"{ctx}, {feel}"
                    if cope:
                        text += f", {cope}"
                    out.append((text + ".", f"tpl_{lang}_1_{ci}"))
    else:
        for ci, state in enumerate(HIGH_STATES[lang]):
            for imp in HIGH_IMPACTS[lang]:
                text = f"{state} {imp}".strip()
                out.append((text + ".", f"tpl_{lang}_2_{ci}"))
    return out


def round_robin_sample(items, n, rng):
    """items: list of (text, group). Take up to n, spreading across groups."""
    by_group = {}
    for text, group in items:
        by_group.setdefault(group, []).append(text)
    for g in by_group:
        rng.shuffle(by_group[g])
    groups = sorted(by_group)
    rng.shuffle(groups)
    picked = []
    while len(picked) < n and any(by_group[g] for g in groups):
        for g in groups:
            if by_group[g] and len(picked) < n:
                picked.append((by_group[g].pop(), g))
    return picked


def main():
    rng = random.Random(SEED)
    rows = []
    seen = set()

    # handwritten
    for label, langs in HANDWRITTEN.items():
        for lang, sentences in langs.items():
            for i, text in enumerate(sentences):
                key = text.strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "text": text.strip(), "label": label, "label_name": LABEL_NAMES[label],
                    "language": lang, "source": "handwritten",
                    "group": f"hw_{lang}_{label}_{i}",
                })

    # templated
    for label in (0, 1, 2):
        for lang in ("english", "hinglish"):
            candidates = [(t, g) for t, g in build_templated(label, lang)
                          if t.strip().lower() not in seen]
            for text, group in round_robin_sample(candidates, TEMPLATED_PER_CELL, rng):
                seen.add(text.strip().lower())
                rows.append({
                    "text": text, "label": label, "label_name": LABEL_NAMES[label],
                    "language": lang, "source": "templated", "group": group,
                })

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    df.insert(0, "id", range(1, len(df) + 1))
    df.to_csv(OUTPUT_PATH, index=False)

    print("=" * 60)
    print("DISTRESS DATASET V3")
    print("=" * 60)
    print("Total:", len(df))
    print("\nBy label:\n", df["label_name"].value_counts().sort_index())
    print("\nBy language:\n", df["language"].value_counts())
    print("\nBy source:\n", df["source"].value_counts())
    print("\nBy label x source:\n", pd.crosstab(df["label_name"], df["source"]))
    print("\nUnique groups:", df["group"].nunique())
    print("\nSaved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
