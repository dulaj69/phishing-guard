"""All warning wording, in English, Sinhala and Singlish.

!!! The Sinhala and Singlish text was written as a first draft and MUST be
checked by a native speaker before the user study. Set NEEDS_REVIEW to False
for a language once it has been checked.
"""

NEEDS_REVIEW = {"en": False, "si": True, "singlish": True}

TITLE = {
    "Critical": {"en": "Stop and verify before acting",
                 "si": "නවතින්න! මෙය බොහෝ දුරට වංචාවකි",
                 "singlish": "Nawathinna! Meka scam ekak wenna godak ida thiyenawa"},
    "High": {"en": "Warning: this looks like a scam",
             "si": "අවවාදයයි: මෙය වංචාවක් ලෙස පෙනේ",
             "singlish": "Awawadayai: meka scam ekak wage"},
    "Medium": {"en": "Be careful with this message",
               "si": "මෙම පණිවිඩය ගැන පරිස්සම් වන්න",
               "singlish": "Me message eka gana parissam wenna"},
    "Low": {"en": "No strong risk detected; authenticity is not verified",
            "si": "මෙම පණිවිඩය සාමාන්‍ය ලෙස පෙනේ",
            "singlish": "Me message eka normal wage"},
}

# One sentence per failed fact check. {value} and {bank} are filled in.
CHECK_FAIL = {
    "official_number": {"en": "{value} is not {bank}'s official number.",
                        "si": "{value} යනු {bank} හි නිල දුරකථන අංකයක් නොවේ.",
                        "singlish": "{value} kiyanne {bank} eke official number ekak nemei."},
    "official_domain": {"en": "{value} is not {bank}'s official website.",
                        "si": "{value} යනු {bank} හි නිල වෙබ් අඩවියක් නොවේ.",
                        "singlish": "{value} kiyanne {bank} eke official website ekak nemei."},
    "bank_rule": {"en": "{bank} never asks for your OTP, PIN or card details by SMS.",
                  "si": "{bank} කිසිවිටෙකත් SMS මගින් ඔබගේ OTP, PIN හෝ කාඩ්පත් විස්තර ඉල්ලන්නේ නැත.",
                  "singlish": "{bank} kawadawath SMS walin obage OTP, PIN, card details illanne na."},
    "sender_id": {"en": "It was not sent from {bank}'s official SMS name.",
                  "si": "මෙය {bank} හි නිල SMS නාමයෙන් එවා නැත.",
                  "singlish": "Meka {bank} eke official SMS name eken ewala na."},
}

ACTION = {
    "share_credential": {"en": "It asks for your OTP, PIN or card details.",
                         "si": "එය ඔබගේ OTP, PIN හෝ කාඩ්පත් විස්තර ඉල්ලයි.",
                         "singlish": "Meka obage OTP, PIN, card details illanawa."},
    "pay": {"en": "It asks you to pay money.", "si": "එය මුදල් ගෙවීමට කියයි.",
            "singlish": "Meka salli gewanna kiyanawa."},
    "install": {"en": "It asks you to install an app.", "si": "එය යෙදුමක් ස්ථාපනය කිරීමට කියයි.",
                "singlish": "Meka app ekak install karanna kiyanawa."},
    "call": {"en": "It asks you to call a number.", "si": "එය දුරකථන අංකයකට ඇමතීමට කියයි.",
             "singlish": "Meka number ekakata call karanna kiyanawa."},
    "reply": {"en": "It asks you to reply.", "si": "එය පිළිතුරු දීමට කියයි.",
              "singlish": "Meka reply karanna kiyanawa."},
    "click": {"en": "It asks you to open a link.", "si": "එය සබැඳියක් විවෘත කිරීමට කියයි.",
              "singlish": "Meka link ekak open karanna kiyanawa."},
}

TACTIC = {
    "URGENCY": {"en": "It rushes you, so you don't have time to check.",
                "si": "පරීක්ෂා කිරීමට කාලය නොදී එය ඔබව ඉක්මන් කරයි.",
                "singlish": "Check karanna welawa nodi ikman karanna kiyanawa."},
    "ACCOUNT_THREAT": {"en": "It scares you with a blocked or suspended account.",
                       "si": "ගිණුම අවහිර වේ යැයි කියමින් එය ඔබව බිය ගන්වයි.",
                       "singlish": "Account eka block wenawa kiyala bayakaranawa."},
    "REWARD_LURE": {"en": "It promises money or a prize to tempt you.",
                    "si": "මුදල් හෝ ත්‍යාග පොරොන්දු වෙමින් එය ඔබව පොළඹවයි.",
                    "singlish": "Salli hari prize ekak denawa kiyala ahu karanawa."},
}

ADVICE = {"en": "Do not call, reply, pay or click anything in this message.",
          "si": "මෙම පණිවිඩයේ ඇති කිසිවකට අමතන්න, පිළිතුරු දෙන්න, ගෙවන්න හෝ ක්ලික් කරන්න එපා.",
          "singlish": "Me message eke thiyena dewal walata call, reply, pay, click karanna epa."}

SAFE_ACTION = {"en": "Call {bank}'s real number: {number}",
               "si": "{bank} හි නිල අංකයට අමතන්න: {number}",
               "singlish": "{bank} eke real number ekata call karanna: {number}"}

VERIFY_FIRST = {"en": "Before you call: which one is {bank}'s real number?",
                "si": "ඇමතීමට පෙර: {bank} හි නිල අංකය කුමක්ද?",
                "singlish": "Call karanna kalin: {bank} eke real number eka mokakda?"}

# 15-second "how the trick works" lessons (inoculation), one per trick.
LESSON = {
    "share_credential": {"en": "Trick: no real bank asks for your OTP. Whoever asks for it wants to empty your account.",
                         "si": "උපක්‍රමය: කිසිදු සැබෑ බැංකුවක් ඔබගේ OTP ඉල්ලන්නේ නැත. එය ඉල්ලන්නේ ඔබගේ ගිණුම හිස් කිරීමටයි.",
                         "singlish": "Trick eka: kisima real bank ekak OTP eka illanne na. Eka illanne obage account eka his karanna."},
    "call": {"en": "Trick: scammers put their own number in the SMS and pretend to be the bank. Always use the number on your card or the bank's website.",
             "si": "උපක්‍රමය: වංචාකරුවන් තමන්ගේ අංකය SMS එකේ දමා බැංකුව ලෙස පෙනී සිටී. සැමවිටම ඔබගේ කාඩ්පතේ හෝ බැංකු වෙබ් අඩවියේ අංකය භාවිතා කරන්න.",
             "singlish": "Trick eka: scammers lage number eka SMS ekata dala bank eka wage kathakaranawa. Hamadama card eke hari bank website eke number eka use karanna."},
    "click": {"en": "Trick: fake links contain the bank's name but go to a different website.",
              "si": "උපක්‍රමය: ව්‍යාජ සබැඳිවල බැංකුවේ නම ඇති නමුත් ඒවා වෙනත් වෙබ් අඩවියකට යයි.",
              "singlish": "Trick eka: fake links wala bank eke nama thiyenawa, eth wena website ekakata yanawa."},
    "pay": {"en": "Trick: real loans and prizes never ask you to pay a fee first.",
            "si": "උපක්‍රමය: සැබෑ ණය හෝ ත්‍යාග සඳහා මුලින් ගාස්තුවක් ගෙවීමට කිසිවිටෙක නොකියයි.",
            "singlish": "Trick eka: real loan hari prize ekakata kalin fee ekak gewanna kiyanne na."},
    "URGENCY": {"en": "Trick: fake deadlines ('within 24 hours') stop you from checking.",
                "si": "උපක්‍රමය: ව්‍යාජ කාල සීමා ('පැය 24ක් ඇතුළත') ඔබට පරීක්ෂා කිරීමට ඉඩ නොදේ.",
                "singlish": "Trick eka: fake deadlines ('paya 24 athule') nisa check karanna welawa na."},
}


# Draft translations: native-speaker review is still required.
UNCERTAIN_TITLE = {"en": "Unable to determine safely", "si": "නිශ්චිත තීරණයක් ලබා දිය නොහැක", "singlish": "Hariyatama theeranaya karanna ba"}
UNCERTAINTY = {
    "en": "We do not have enough verified evidence. Check through your bank's app or the number on your card before acting.",
    "si": "තහවුරු කළ තොරතුරු ප්‍රමාණවත් නැත. ක්‍රියා කිරීමට පෙර බැංකු යෙදුමෙන් හෝ ඔබේ කාඩ්පතේ අංකයෙන් පරීක්ෂා කරන්න.",
    "singlish": "Thahawuru karapu thorathuru madi. Kriya karanna kalin bank app eken hari card eke number eken hari balanna.",
}
INDEPENDENT_CHECK = {
    "en": "Before seeing our advice, check the requested action and contact details against your bank app or card. What did you check?",
    "si": "අපගේ උපදෙස් බැලීමට පෙර ඉල්ලූ ක්‍රියාව සහ අංක ඔබේ බැංකු යෙදුම හෝ කාඩ්පත සමඟ පරීක්ෂා කරන්න.",
    "singlish": "Ape upades balanna kalin illana de saha numbers bank app eka hari card eka hari ekka balanna.",
}

CHECK_FAIL["bank_rule"] = {
    "en": "The requested action conflicts with a published bank policy.",
    "si": "ඉල්ලා ඇති ක්‍රියාව ප්‍රකාශිත බැංකු ප්‍රතිපත්තියකට පටහැනිය.",
    "singlish": "Illana kriyawa bank eke prakashitha prathipaththiyakata patihaniyi.",
}
