from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.keyboards.menu import main_menu


router = Router()


GUIDE_HOME_TEXT = (
    "📖 <b>FOYDALANISH QO‘LLANMASI</b>\n\n"
    "ZevintorTunnel’dan foydalanish bo‘yicha bosqichma-bosqich qo‘llanma.\n\n"
    "Kerakli bo‘limni tanlang:"
)


GUIDE_PAGES = {
    "start": (
        "🚀 <b>BOSHLASH</b>\n\n"
        "ZevintorTunnel’dan foydalanishni boshlash juda oson.\n\n"
        "1️⃣ <b>Botni ishga tushiring</b>\n"
        "/start buyrug‘i orqali botni ishga tushiring va ro‘yxatdan o‘ting.\n\n"
        "2️⃣ <b>🎁 Bonuslaringizni tekshiring</b>\n"
        "Yangi foydalanuvchi sifatida sizga Welcome Bonus taqdim etilishi mumkin.\n"
        "Bonusni olish uchun 🎁 Bonusni olish tugmasidan foydalaning.\n\n"
        "3️⃣ <b>🛒 Xizmatni tanlang</b>\n"
        "VPN’dan foydalanish uchun kerakli obunani sotib olishingiz yoki mavjud bonus xizmatingizdan foydalanishingiz mumkin.\n\n"
        "4️⃣ <b>🔐 VPN xizmatini faollashtiring</b>\n"
        "Faol xizmat uchun VPN hisobini yarating va ulanish ma’lumotlarini oling.\n\n"
        "5️⃣ <b>📱 Happ ilovasiga ulang</b>\n"
        "Olingan VPN ma’lumotlarini Happ ilovasiga qo‘shing.\n\n"
        "6️⃣ <b>🟢 VPN’ni ishga tushiring</b>\n"
        "Happ’da ZevintorTunnel profilini tanlang va VPN ulanishini yoqing.\n\n"
        "🎁 <b>Muhim:</b>\n"
        "ZevintorTunnel’da Welcome, Promo, Referral va Admin bonuslari mavjud. "
        "Barcha bonuslaringizni 🎁 Mening bonuslarim bo‘limidan boshqarishingiz mumkin.\n\n"
        "ℹ️ Har bir bosqich bo‘yicha batafsil ko‘rsatma uchun qo‘llanmaning tegishli bo‘limini tanlang."
    ),
    "welcome": (
        "🎁 <b>WELCOME BONUS</b>\n\n"
        "ZevintorTunnel’ga yangi qo‘shilgan foydalanuvchilar uchun maxsus Welcome Bonus mavjud. 🎉\n\n"
        "🎁 <b>Siz olasiz:</b>\n"
        "⏳ 3 kunlik xizmat\n"
        "📦 3 GiB trafik\n\n"
        "<b>Bonusni qanday olish mumkin?</b>\n\n"
        "1️⃣ Botni /start orqali ishga tushiring.\n"
        "2️⃣ 🎁 Welcome Bonus bo‘limiga kiring.\n"
        "3️⃣ 🎁 Bonusni olish tugmasini bosing.\n"
        "4️⃣ Bonus faollashgach, undan foydalanishni boshlashingiz mumkin.\n\n"
        "📌 <b>Muhim:</b>\n"
        "• Welcome Bonus har bir foydalanuvchiga faqat bir marta beriladi.\n"
        "• Bonus /start bosilganda avtomatik berilmaydi.\n"
        "• Bonusni olish uchun telefon raqami majburiy emas.\n"
        "• Bonus 3 GiB trafik bilan cheklangan.\n"
        "• 3 GiB trafik tugagach, Welcome Bonus yakunlanadi.\n\n"
        "💡 Bonus faol bo‘lgach, VPN xizmatidan foydalanish uchun keyingi qo‘llanma bosqichlariga o‘ting."
    ),
    "buy": (
        "🛒 <b>OBUNA SOTIB OLISH</b>\n\n"
        "ZevintorTunnel VPN xizmatidan foydalanish uchun o‘zingizga mos obunani tanlashingiz mumkin.\n\n"
        "<b>Qanday sotib olinadi?</b>\n\n"
        "1️⃣ Asosiy menyudan 🛒 Obuna sotib olish bo‘limiga kiring.\n"
        "2️⃣ O‘zingizga mos tarifni tanlang.\n"
        "3️⃣ Tarifning muddati va narxini tekshiring.\n"
        "4️⃣ To‘lovni amalga oshiring.\n"
        "5️⃣ To‘lov muvaffaqiyatli yakunlangach, obunangiz tizimga qo‘shiladi.\n\n"
        "📋 Obuna holatini 👤 Mening obunam bo‘limidan ko‘rishingiz mumkin.\n\n"
        "ℹ️ Agar hozirda boshqa xizmat faol bo‘lsa, yangi xizmat darhol uning o‘rnini bosmaydi — "
        "xizmatlar belgilangan navbat asosida boshqariladi.\n\n"
        "🎁 Bonuslaringiz esa alohida 🎁 Mening bonuslarim bo‘limida ko‘rsatiladi."
    ),
    "vpn": (
        "🔐 <b>VPN XIZMATINI FAOLLASHTIRISH</b>\n\n"
        "Obuna yoki bonus asosidagi xizmat faol bo‘lgach, undan foydalanish uchun VPN hisobini yaratishingiz mumkin.\n\n"
        "<b>VPN hisobini qanday yaratish mumkin?</b>\n\n"
        "1️⃣ 👤 Mening obunam bo‘limiga kiring.\n"
        "2️⃣ 🟢 Hozirgi xizmat bo‘limida faol xizmatingizni tekshiring.\n"
        "3️⃣ Agar VPN hisob hali yaratilmagan bo‘lsa, VPN hisobini yaratish tugmasini bosing.\n"
        "4️⃣ Hisob muvaffaqiyatli yaratilgach, sizga VPN ulanish ma’lumotlari ko‘rsatiladi.\n\n"
        "🔗 <b>VLESS havola</b>\n"
        "VPN’ga ulanish uchun foydalaniladigan VLESS havolani ko‘rishingiz mumkin. "
        "Havola ustiga bosib, uni nusxalashingiz va Happ ilovasiga qo‘shishingiz mumkin.\n\n"
        "📥 <b>Obuna havolasi</b>\n"
        "Obuna havolasi orqali VPN profilini mos VPN ilovasiga qo‘shishingiz mumkin.\n\n"
        "📱 Keyingi bosqichda VPN ma’lumotlarini Happ ilovasiga qanday ulashni ko‘rib chiqamiz.\n\n"
        "ℹ️ VPN hisobingizni qayta-qayta yaratish shart emas. Hisob mavjud bo‘lsa, "
        "👤 Mening obunam bo‘limida uning ma’lumotlari ko‘rsatiladi."
    ),
    "happ": (
        "📱 <b>HAPP ILOVASI</b>\n\n"
        "ZevintorTunnel VPN xizmatidan foydalanish uchun Happ ilovasidan foydalanishingiz mumkin.\n\n"
        "<b>Happ bilan ishlashni boshlash:</b>\n\n"
        "1️⃣ Telefoningizga Happ ilovasini o‘rnating.\n"
        "2️⃣ Ilovani ishga tushiring.\n"
        "3️⃣ ZevintorTunnel’dan VPN xizmatini faollashtiring va ulanish ma’lumotlarini oling.\n"
        "4️⃣ Keyingi 🔗 Happ'ga ulash bo‘limidagi ko‘rsatmalar orqali ZevintorTunnel’ni Happ ilovasiga qo‘shing.\n"
        "5️⃣ Profil qo‘shilgach, undan VPN ulanishi uchun foydalanishingiz mumkin.\n\n"
        "🔐 <b>Eslatma:</b>\n"
        "VPN ma’lumotlaringizni boshqa shaxslarga bermang.\n\n"
        "➡️ Happ’ga ZevintorTunnel’ni ulash bo‘yicha batafsil ko‘rsatma uchun "
        "🔗 Happ'ga ulash bo‘limiga o‘ting."
    ),
    "happ_connect": (
        "🔗 <b>HAPP'GA ULASH</b>\n\n"
        "ZevintorTunnel VPN xizmatini Happ ilovasiga ulash uchun quyidagi amallarni bajaring.\n\n"
        "1️⃣ 👤 Mening obunam bo‘limiga kiring.\n\n"
        "2️⃣ Faol xizmatingizdagi VLESS havola ustiga bosing va uni nusxalang.\n\n"
        "3️⃣ Happ ilovasini oching.\n\n"
        "📥 <b>1-usul — pastdagi tugma orqali</b>\n\n"
        "4️⃣ Happ asosiy ekranining pastki qismidagi «Из буфера» tugmasini bosing.\n\n"
        "5️⃣ Nusxalangan VPN konfiguratsiyasi Happ’ga qo‘shiladi.\n\n"
        "➕ <b>2-usul — «+» tugmasi orqali</b>\n\n"
        "4️⃣ Happ asosiy ekranidagi ➕ tugmasini bosing.\n\n"
        "5️⃣ Ochilgan menyudan «Вставить из буфера обмена» bandini tanlang.\n\n"
        "6️⃣ Nusxalangan VPN konfiguratsiyasi Happ’ga qo‘shiladi.\n\n"
        "7️⃣ Qo‘shilgan profilni tanlang va VPN’ni ishga tushiring.\n\n"
        "🔐 <b>Muhim:</b>\n"
        "VLESS havolangiz maxsus VPN konfiguratsiyangiz hisoblanadi. Uni boshqa shaxslarga bermang."
    ),
    "enable": (
        "🟢 <b>VPN'NI YOQISH</b>\n\n"
        "ZevintorTunnel konfiguratsiyasi Happ ilovasiga qo‘shilgach, VPN’dan foydalanishni boshlashingiz mumkin.\n\n"
        "1️⃣ Happ ilovasida qo‘shilgan ZevintorTunnel profilingizni tanlang.\n"
        "2️⃣ Profilning ulanishini ishga tushiring.\n"
        "3️⃣ VPN ulanishi faol bo‘lgach, internetdan VPN orqali foydalanishingiz mumkin.\n\n"
        "🔒 <b>Muhim:</b>\n"
        "VPN ishlashi uchun ZevintorTunnel xizmatining amal qilish muddati tugamagan bo‘lishi kerak.\n\n"
        "📊 Xizmat muddati va holatini botdagi 👤 Mening obunam bo‘limidan tekshirishingiz mumkin.\n\n"
        "🎁 Agar bonus asosida xizmatdan foydalanayotgan bo‘lsangiz, bonusning holati va qolgan ma’lumotlarini "
        "🎁 Mening bonuslarim bo‘limidan ko‘rishingiz mumkin.\n\n"
        "⚠️ <b>Mobil internetdagi cheklovlar haqida</b>\n\n"
        "Ayrim mobil operatorlar <b>xavfsizlik uchun</b> ba’zi hududlarda internetga <b>qisman cheklovlar</b> "
        "o‘rnatishi mumkin. Bunday holatda oddiy internet ishlayotgan bo‘lsa ham, VPN ulanishi ishlamasligi yoki "
        "barqaror ishlamasligi mumkin.\n\n"
        "📶 Bu holat VPN hisobingiz yoki obunangiz bilan bog‘liq bo‘lmasligi mumkin — muammo mobil operator "
        "tomonidan qo‘yilgan tarmoq cheklovi sababli yuzaga keladi.\n\n"
        "📡 Agar mobil internet orqali VPN ulanmasa, <b>Wi-Fi tarmog‘i orqali ulanishni sinab ko‘ring</b>. "
        "Agar Wi-Fi orqali VPN ishlasa, muammo mobil tarmoqdagi cheklov bilan bog‘liq bo‘lishi ehtimoli yuqori.\n\n"
        "💡 VPN ishlamay qolganida avvalo boshqa internet tarmog‘i, masalan Wi-Fi orqali tekshirib ko‘rish tavsiya etiladi.\n\n"
        "⚠️ Agar VPN ulanmasa, 📞 Yordam bo‘limi orqali biz bilan bog‘laning."
    ),
    "subscription": (
        "👤 <b>MENING OBUNAM</b>\n\n"
        "Bu bo‘lim orqali ZevintorTunnel xizmatlaringizni boshqarishingiz va VPN ulanish ma’lumotlaringizni ko‘rishingiz mumkin.\n\n"
        "🟢 <b>Hozirgi xizmat</b>\n"
        "Ayni paytda faol bo‘lgan xizmatingiz haqida ma’lumot olasiz:\n"
        "📦 Obuna yoki\n"
        "📅 Kunlik obuna\n"
        "Bu yerda tarif, narx, boshlanish sanasi, tugash sanasi va qolgan muddat ko‘rsatiladi.\n\n"
        "🔐 <b>VPN ma’lumotlari</b>\n"
        "VPN hisobingiz yaratilgach, username va VLESS havolangiz shu bo‘limda ko‘rsatiladi.\n\n"
        "📋 <b>Keyingi xizmat</b>\n"
        "Agar sizda navbatdagi xizmat mavjud bo‘lsa, bu yerda faqat eng yaqin keyingi xizmat ko‘rsatiladi.\n\n"
        "📜 <b>Obunalar tarixi</b>\n"
        "Oldingi xizmatlaringiz tarixini ko‘rishingiz mumkin.\n\n"
        "🎁 <b>Bonuslar</b>\n"
        "Welcome, Promo, Referral va Admin bonuslarining batafsil ma’lumotlari bu bo‘limda emas, "
        "🎁 Mening bonuslarim bo‘limida ko‘rsatiladi.\n\n"
        "💡 <b>VPN’ga ulanish</b>\n"
        "VLESS havolasi ustiga bosib, uni nusxalashingiz va Happ ilovasiga qo‘shishingiz mumkin.\n\n"
        "📥 Shuningdek, VPN profilingizni Obuna havolasi orqali ham olishingiz mumkin."
    ),
    "bonuses": (
        "🎁 <b>MENING BONUSLARIM</b>\n\n"
        "ZevintorTunnel’dagi barcha bonuslaringizni shu bo‘lim orqali ko‘rishingiz mumkin.\n\n"
        "🎁 <b>Welcome Bonus</b>\n"
        "Yangi foydalanuvchilar uchun beriladigan bonus.\n"
        "⏳ 3 kun\n"
        "📦 3 GiB trafik\n\n"
        "🎟 <b>Promo Bonus</b>\n"
        "Promo kod orqali olingan bonus.\n"
        "Promo kod, bonus muddati va holati haqida ma’lumot ko‘rsatiladi.\n\n"
        "👥 <b>Referral Bonus</b>\n"
        "Siz taklif qilgan foydalanuvchining birinchi oylik obunasi xarididan keyin beriladigan bonus.\n"
        "🎁 Oddiy referral — 3 kun\n"
        "⭐ Har 5-chi referral — 7 kun\n\n"
        "👨‍💼 <b>Admin Bonus</b>\n"
        "Administrator tomonidan berilgan bonus.\n"
        "Bonus muddati va berilish sababi ko‘rsatilishi mumkin.\n\n"
        "📊 <b>Bonus holatlari</b>\n"
        "🟢 Faol — bonus hozir ishlatilmoqda.\n"
        "⏳ Kutilmoqda — bonus navbatda turibdi va hali faollashmagan.\n"
        "⚪ Tugagan — bonusning amal qilish muddati tugagan.\n"
        "🚫 Bekor qilingan — bonus bekor qilingan.\n\n"
        "📜 <b>Bonuslar tarixi</b>\n"
        "Olingan bonuslaringiz tarixini ham ko‘rishingiz mumkin.\n\n"
        "💡 <b>Muhim:</b>\n"
        "Kutilayotgan bonus vaqtni sarflamaydi. Bonus faollashgandan keyingina uning amal qilish muddati boshlanadi."
    ),
    "referral": (
        "👥 <b>REFERRAL BONUS</b>\n\n"
        "Do‘stlaringizni ZevintorTunnel’ga taklif qiling va referral bonuslariga ega bo‘ling. 🎁\n\n"
        "<b>Referral bonusi qanday ishlaydi?</b>\n\n"
        "1️⃣ Referral orqali yangi foydalanuvchini ZevintorTunnel’ga taklif qilasiz.\n"
        "2️⃣ Taklif qilingan foydalanuvchi botdan foydalanishni boshlaydi.\n"
        "3️⃣ U o‘zining birinchi oylik Paid obunasini sotib olgach, sizga Referral Bonus beriladi.\n\n"
        "🎁 <b>Bonus miqdori:</b>\n"
        "• 1-, 2-, 3-, 4-chi referral — 3 kun\n"
        "• Har 5-chi referral — 7 kun\n\n"
        "⭐ <b>Masalan:</b>\n"
        "#1 → 3 kun\n"
        "#2 → 3 kun\n"
        "#3 → 3 kun\n"
        "#4 → 3 kun\n"
        "#5 → 7 kun\n"
        "#6 → 3 kun\n"
        "...\n"
        "#10 → 7 kun\n\n"
        "📌 <b>Muhim:</b>\n"
        "• Foydalanuvchi shunchaki /start qilgani uchun referral bonusi berilmaydi.\n"
        "• Faqat birinchi oylik Paid obuna xaridi hisoblanadi.\n"
        "• Kunlik obuna referral bonusini faollashtirmaydi.\n"
        "• Bitta taklif qilingan foydalanuvchi faqat bir marta referral bonus olib keladi.\n"
        "• O‘zingizni o‘zingiz referral qilish mumkin emas.\n\n"
        "🎁 Olingan referral bonuslarini 🎁 Mening bonuslarim bo‘limida ko‘rishingiz mumkin."
    ),
    "promo": (
        "🎟 <b>PROMO KOD</b>\n\n"
        "ZevintorTunnel’da promo kod orqali qo‘shimcha bonus olish mumkin.\n\n"
        "<b>Promo kodni qanday ishlatish mumkin?</b>\n\n"
        "1️⃣ Asosiy menyudan 🎟 Promo kod bo‘limiga kiring.\n"
        "2️⃣ Sizga berilgan promo kodni kiriting.\n"
        "3️⃣ Kod tekshiriladi va shartlarga mos kelsa, promo bonusingiz beriladi.\n"
        "4️⃣ Olingan bonusni 🎁 Mening bonuslarim bo‘limida ko‘rishingiz mumkin.\n\n"
        "📌 <b>Muhim:</b>\n"
        "• Promo kod faqat belgilangan shartlar asosida ishlaydi.\n"
        "• Ayrim promo kodlarda foydalanish soni cheklangan bo‘lishi mumkin.\n"
        "• Bitta promo koddan bir foydalanuvchi uchun foydalanish soni ham cheklangan bo‘lishi mumkin.\n"
        "• Promo kodning amal qilish muddati bo‘lishi mumkin.\n"
        "• Promo kodni kampaniya muddati tugashidan oldin ishlatish kerak.\n"
        "• Promo kod orqali olingan bonus darhol yoki navbat asosida faollashishi mumkin.\n\n"
        "🎁 Promo bonusining holati, muddati va boshqa ma’lumotlarini 🎁 Mening bonuslarim bo‘limidan ko‘rishingiz mumkin."
    ),
    "help": (
        "📞 <b>YORDAM</b>\n\n"
        "Savolingiz yoki muammoingiz bo‘lsa, biz bilan bog‘lanishingiz mumkin.\n\n"
        "🛠 <b>Obuna, to‘lov, VPN xizmati yoki botdan foydalanish bo‘yicha yordam olish uchun</b> "
        "Telefon raqamingizni ulashish tugmasini bosing.\n\n"
        "🔒 <b>Telefon raqamingiz</b> faqat murojaatingizni aniqlash uchun ishlatiladi va boshqa foydalanuvchilarga ko‘rsatilmaydi.\n\n"
        "📩 Muammoingizni imkon qadar aniq yozing — bu yordam ko‘rsatish jarayonini tezlashtiradi."
    ),
}


GUIDE_MENU = [
    ("🚀 Boshlash", "start"),
    ("🎁 Welcome Bonus", "welcome"),
    ("🛒 Obuna sotib olish", "buy"),
    ("🔐 VPN xizmatini faollashtirish", "vpn"),
    ("📱 Happ ilovasi", "happ"),
    ("🔗 Happ'ga ulash", "happ_connect"),
    ("🟢 VPN'ni yoqish", "enable"),
    ("👤 Mening obunam", "subscription"),
    ("🎁 Mening bonuslarim", "bonuses"),
    ("👥 Referral Bonus", "referral"),
    ("🎟 Promo kod", "promo"),
    ("📞 Yordam", "help"),
]


def guide_home_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for index in range(0, len(GUIDE_MENU), 2):
        row = []
        for text, key in GUIDE_MENU[index:index + 2]:
            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"guide:{key}",
                )
            )
        rows.append(row)

    rows.append([
        InlineKeyboardButton(
            text="🏠 Asosiy menyu",
            callback_data="user_main_menu",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def guide_page_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩ Ortga",
                    callback_data="guide:home",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Asosiy menyu",
                    callback_data="user_main_menu",
                ),
            ],
        ]
    )


@router.message(F.text == "📖 Foydalanish qo'llanmasi")
async def guide_handler(message: Message):
    await message.answer(
        GUIDE_HOME_TEXT,
        parse_mode="HTML",
        reply_markup=guide_home_keyboard(),
    )


@router.callback_query(F.data == "guide:home")
async def guide_home(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        GUIDE_HOME_TEXT,
        parse_mode="HTML",
        reply_markup=guide_home_keyboard(),
    )


@router.callback_query(F.data.startswith("guide:"))
async def guide_page(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    text = GUIDE_PAGES.get(key)

    if text is None:
        await callback.answer("Bo‘lim topilmadi.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=guide_page_keyboard(),
    )
