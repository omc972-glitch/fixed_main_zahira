# -*- coding: utf-8 -*-
"""Zahira — deney simülasyonları için asistan konuşmaları.

Her satır (sprite, metin) çiftidir. Sprite adı SPRITE_FILES anahtarlarından biridir:
  idle        sakin/nötr, selamlama
  idle_hand   rahat anlatım, açıklama
  think       düşünme, uyarı, dikkat gerektiren durum
  hold_flask  reaktif/numune/güvenlik, kimyasal işlem anlatımı
  point       grafiğe/sonuca/düzeneğe dikkat çekme
  idea        ipucu, temel kavram, formül
  cheer       başarı, deney sonu

Metinlerdeki {isim} alanları .format(**kwargs) ile doldurulur; hangi alanların
gerektiği her deneyin başındaki yorumda yazıyor.

Kullanım:
    from zahira_konusmalar import Zahira
    z = Zahira("titrasyon")
    for line in z.say("intro"):
        print(line.sprite, line.text)
"""
import os
from collections import namedtuple

Line = namedtuple("Line", "sprite text")

SPRITE_FILES = {
    "idle": "zahira_idle.png",
    "idle_hand": "zahira_idle_hand.png",
    "think": "zahira_think.png",
    "hold_flask": "zahira_hold_flask.png",
    "point": "zahira_point.png",
    "idea": "zahira_idea.png",
    "cheer": "zahira_cheer.png",
}


def sprite_path(name, folder="zahira_sprites"):
    return os.path.join(folder, SPRITE_FILES[name])


# ---------------------------------------------------------------------------
# Genel
# ---------------------------------------------------------------------------
GENEL = {
    "reset": [("idle", "Simülasyonu sıfırladım. Parametreleri ayarlayıp tekrar başlatabilirsin.")],
    "tips": [
        ("idea", "İpucu: kaydırıcıları değiştirip aynı deneyi yeniden çalıştır, sonuçların nasıl değiştiğine bak."),
        ("idle_hand", "Deneyin bilgi sayfasında malzeme listesi ve işlem adımları yazıyor."),
    ],
}

# ---------------------------------------------------------------------------
# Deneyler
# "progress": (eşik 0-1, sprite, metin). Eşik, ilerleme çubuğu o değeri geçince bir kez gösterilir.
# ---------------------------------------------------------------------------
DIALOGUES = {

    # alanlar: veq, ph_eq, ph_half
    "titrasyon": {
        "intro": [
            ("idle", "Merhaba, ben Zahira! Bugün asit–baz titrasyonu yapıyoruz."),
            ("hold_flask", "Erlenmayerde asit ve 2–3 damla fenolftalein var, büretteki ise NaOH."),
            ("idea", "Fenolftalein pH 8,2'nin üstünde pembeleşir; dönüm noktasını rengine bakarak yakalarız."),
        ],
        "start": [("point", "Musluğu açıyorum! Sağdaki grafikte pH'ın NaOH eklendikçe nasıl değiştiğini izle.")],
        "progress": [
            (0.10, "idle_hand", "Başlangıçta pH yavaş yükselir. Zayıf asit seçtiysen burası tampon bölgesi."),
            (0.45, "think", "Eğri hâlâ yataya yakın, ama eşdeğerlik noktasına yaklaştıkça pH birden sıçrayacak."),
        ],
        "equivalence": [
            ("point", "Eşdeğerlik noktası! {veq:.2f} mL NaOH eklenince pH {ph_eq:.2f} oldu."),
            ("idea", "Burada asidin mol sayısı bazın mol sayısına eşit: Ca·Va = Cb·Vb."),
        ],
        "finish_weak": [
            ("cheer", "Titrasyon tamam! Eşdeğerlik hacmi {veq:.2f} mL."),
            ("idea", "Yarı eşdeğerlikte pH {ph_half:.2f} çıktı. Bu değer asidin pKa'sına eşit (asetik asit için yaklaşık 4,76)."),
            ("idle_hand", "Zayıf asitte eşdeğerlik pH'ı 7'nin üstünde çıkar, çünkü asetat iyonu hafif baziktir."),
        ],
        "finish_strong": [
            ("cheer", "Titrasyon tamam! Eşdeğerlik hacmi {veq:.2f} mL."),
            ("idea", "Güçlü asit–güçlü baz titrasyonunda eşdeğerlik pH'ı yaklaşık 7 çıkar ve sıçrama çok diktir."),
        ],
        "warn_not_reached": [("think", "Eşdeğerlik noktasına ulaşamadık. Eklenecek titrant hacmini artır ya da NaOH'ı daha derişik yap.")],
        "error_conc": [("think", "Derişimler sıfırdan büyük olmalı. Kaydırıcıları bir kontrol eder misin?")],
    },

    # alanlar: cs_calc, cs_true, r2
    "bradford": {
        "intro": [
            ("idle", "Merhaba! Bradford yöntemiyle protein derişimini bulacağız."),
            ("hold_flask", "Coomassie boyası proteine bağlanınca maksimum absorbansı 465 nm'den 595 nm'ye kayıyor."),
            ("idea", "Önce BSA standartlarıyla kalibrasyon doğrusu çizeceğiz, sonra numuneyi o doğruya yerleştireceğiz."),
        ],
        "start": [("point", "Tüpleri sırayla hazırlıyorum. Üstte renk koyulaşıyor, altta kalibrasyon noktaları beliriyor.")],
        "progress": [
            (0.25, "idle_hand", "Derişim arttıkça tüpler daha koyu mavi oluyor; bu renk değişimi absorbansla orantılı."),
            (0.60, "think", "Noktalar tam bir doğru üzerinde olmayabilir; ölçüm gürültüsü her tüpte biraz sapma yaratır."),
            (0.90, "point", "Son tüp numune. Şimdi onun absorbansını kalibrasyon doğrusuna taşıyacağım."),
        ],
        "finish": [
            ("cheer", "Hesap tamam! Numunenin derişimi {cs_calc:.3f} mg/mL çıktı."),
            ("point", "Gerçek değer {cs_true:.3f} mg/mL idi; kalibrasyon doğrusunun R² değeri {r2:.4f}."),
            ("idea", "R² 1'e ne kadar yakınsa kalibrasyon o kadar güvenilir."),
        ],
        "warn_range": [("think", "Numune kalibrasyon aralığının dışında çıktı. Seyrelt ve yeniden ölç, yoksa doğrusal bölgeden çıkmış oluruz.")],
        "tip_noise": [("idea", "Gürültüyü artırırsan R² düşer ve bağıl hata büyür. Pipetleme hassasiyeti bu yüzden önemli.")],
    },

    # alanlar: rf1 (tek bileşen), dmin
    "kromatografi": {
        "intro": [
            ("idle", "Merhaba! İnce tabaka kromatografisiyle karışımı bileşenlerine ayıracağız."),
            ("hold_flask", "Sabit faz polar silika, hareketli faz çözücü. Polar bileşenler silikaya daha çok tutunur."),
            ("idea", "Rf = bileşenin aldığı yol / çözücü cephesinin aldığı yol."),
        ],
        "start": [("point", "Plakayı tanka koydum. Çözücü kılcallıkla yukarı çıkıyor ve lekeleri yanında taşıyor.")],
        "progress": [
            (0.30, "idle_hand", "Apolar bileşenler çözücüyle birlikte hızlı yükseliyor."),
            (0.65, "think", "Polar bileşenler silikaya yapışıp geride kalıyor; ayrışma tam olarak bu farktan geliyor."),
            (0.95, "point", "Çözücü cephesi üste yaklaştı. Plakayı çıkarıp cepheyi işaretleme zamanı."),
        ],
        "finish_iyi": [
            ("cheer", "Lekeler güzel ayrıldı! En küçük ΔRf {dmin:.2f}."),
            ("idea", "ΔRf 0,1'in üstündeyse bileşenleri rahatça ayırt edebiliriz."),
        ],
        "finish_orta": [
            ("idle_hand", "Ayrışma fena değil ama bazı lekeler birbirine yakın (ΔRf {dmin:.2f})."),
            ("think", "Çözücü polarlığını biraz değiştirirsen aralık açılabilir."),
        ],
        "finish_kotu": [
            ("think", "Lekeler üst üste biniyor (ΔRf {dmin:.2f})."),
            ("idea", "Çözücü polarlığını değiştir; polar çözücü tüm Rf değerlerini artırır."),
        ],
        "finish_tek": [("idle_hand", "Tek bileşen var, ayrışma kalitesi ölçülemez. Rf değeri {rf1:.2f}.")],
        "warn_rf": [
            ("point", "Bazı Rf değerleri 0,2–0,8 aralığının dışında."),
            ("idea", "İdeal ayrım için çözücü polarlığını ayarla ki Rf'ler bu aralığa girsin."),
        ],
    },

    # alanlar: limname, conv, theo, prac, yield_pct
    "aspirin": {
        "intro": [
            ("idle", "Merhaba! Salisilik asitten aspirin (asetilsalisilik asit) sentezleyeceğiz."),
            ("hold_flask", "Salisilik asidin fenolik –OH grubu asetik anhidritle asetilleniyor; yan ürün asetik asit."),
            ("idea", "Teorik verim, limitli reaktife göre hesaplanır."),
            ("hold_flask", "Asetik anhidrit ve H₂SO₄ aşındırıcı: çeker ocakta, eldiven ve gözlükle çalış."),
        ],
        "start_cat": [("point", "Katalizör olarak H₂SO₄ ekledim. Hız sabiti sıcaklıkla Arrhenius denklemine göre artıyor.")],
        "start_nocat": [("think", "Katalizör yok, reaksiyon belirgin şekilde yavaş. Dönüşüm eğrisi yavaş yükselecek.")],
        "progress": [
            (0.30, "idle_hand", "Sıcaklık yükseldikçe k artıyor, o yüzden grafikte dönüşüm hızlanıyor."),
            (0.70, "think", "Eğri yataylaşıyorsa limitli reaktif bitmek üzere demektir."),
        ],
        "finish": [
            ("cheer", "Reaksiyon bitti, buz banyosunda kristallendiriyorum!"),
            ("point", "Limitli reaktif: {limname}. Dönüşüm %{conv:.1f}."),
            ("idea", "Teorik verim {theo:.3f} g, tahmini pratik verim {prac:.3f} g (%{yield_pct:.1f}). Fark süzme ve yıkama kayıplarından gelir."),
        ],
        "warn_high_T": [
            ("think", "Sıcaklık 90 °C'nin üstünde; bozunma ve yan ürün oluşumu verimi düşürüyor."),
            ("idea", "80 °C civarında kalmak genelde daha dengeli."),
        ],
        "error_amount": [("think", "Reaktif miktarları sıfırdan büyük olmalı.")],
    },

    # alanlar: name, conv, yield_pct, mp
    "coumarin": {
        "intro_resorsinol": [
            ("idle", "Merhaba! Pechmann kondenzasyonuyla kumarin sentezliyoruz."),
            ("idea", "Resorsinol elektronca çok zengin bir fenol; reaksiyonu hızlı verir."),
            ("hold_flask", "H₂SO₄'ü buz banyosunda soğuttum. Karışımı damla damla ekleyeceğiz, çok aşındırıcı!"),
        ],
        "intro_fenol": [
            ("idle", "Merhaba! Pechmann kondenzasyonuyla kumarin sentezliyoruz."),
            ("think", "Sade fenol resorsinole göre çok daha az reaktif; reaksiyon yavaş ilerler ve verim düşük kalabilir."),
            ("hold_flask", "H₂SO₄'ü buz banyosunda soğuttum. Karışımı damla damla ekleyeceğiz, çok aşındırıcı!"),
        ],
        "start": [("point", "Sol altta mekanizma adımlarını, sağda tür dağılımını izle.")],
        "step_0": [("idle_hand", "Adım 1: Asit, β-ketoesteri protonluyor.")],
        "step_1": [("point", "Adım 2: Fenolle transesterleşme, yani kondenzasyon.")],
        "step_2": [("idea", "Adım 3: Elektrofilik aromatik halka kapanması; halka burada oluşuyor.")],
        "step_3": [("think", "Adım 4: Dehidrasyonla su çıkıyor ve aromatik kumarin oluşuyor.")],
        "finish": [
            ("cheer", "Sentez tamam! Ürün: {name}."),
            ("point", "Dönüşüm %{conv:.1f}, tahmini izole verim %{yield_pct:.1f}."),
            ("idea", "Erime noktası {mp}. UV lambada mavi floresans verir; ürünü böyle de doğrulayabilirsin."),
        ],
        "warn_ratio": [("think", "β-ketoester limitli reaktif oldu. Oranı 1'in üstüne çıkarırsan dönüşüm artar.")],
        "warn_side": [("think", "Sıcaklık çok yüksek; kömürleşme ve yan ürün oluşuyor, verim düşüyor.")],
    },

    # alanlar: dom_name, color, lmax, amax, log_beta4
    "bakir_kompleks": {
        "intro": [
            ("idle", "Merhaba! Bakır(II) iyonuna adım adım amonyak ekleyip amin kompleksini oluşturacağız."),
            ("idea", "NH₃ ligandı bağlandıkça d–d geçişi kısa dalga boyuna kayar: λmax yaklaşık 800 nm'den 610 nm'ye iner."),
            ("hold_flask", "Gerçek deneyde önce mavi Cu(OH)₂ çökeleği görülür; simülasyonda onu hesaba katmıyoruz."),
            ("hold_flask", "Derişik amonyak buharı tahriş edici, çeker ocakta çalış."),
        ],
        "start": [("point", "Solda çözelti rengi, sağda tür dağılımı, altta absorbans spektrumu var.")],
        # baskın tür değiştiğinde (indeks: 0=Cu²⁺ ... 4=[Cu(NH₃)₄]²⁺)
        "species_0": [("idle_hand", "Şu an baskın tür serbest Cu²⁺(aq): açık mavi.")],
        "species_1": [("point", "[Cu(NH₃)]²⁺ baskın hale geldi; renk biraz koyulaştı.")],
        "species_2": [("idea", "[Cu(NH₃)₂]²⁺ baskın; spektrum kısa dalga boyuna kayıyor.")],
        "species_3": [("think", "[Cu(NH₃)₃]²⁺ baskın. Kararlılık sabitleri azalıyor, her basamak bir öncekinden biraz daha zor.")],
        "species_4": [("hold_flask", "[Cu(NH₃)₄]²⁺ baskın: koyu lacivert, klasik tetra amin bakır(II) rengi!")],
        "finish": [
            ("cheer", "Kompleks oluştu! Baskın tür {dom_name}."),
            ("point", "λmax {lmax:.0f} nm, Amax {amax:.3f}. Renk: {color}."),
            ("idea", "log β₄ = {log_beta4:.2f}; bu yüksek değer kompleksin çok kararlı olduğunu gösterir."),
        ],
        "finish_tetra": [("idle_hand", "Gerçek deneyde etanol ekleyerek bu kompleksi kristallendirirsin.")],
    },

    # alanlar: qeq, E, mc
    "egdma_hidrojel": {
        "intro": [
            ("idle", "Merhaba! EGDMA ile çapraz bağlı bir (p)HEMA hidrojeli hazırlayacağız."),
            ("hold_flask", "EGDMA çapraz bağlayıcı: zincirleri birbirine bağlayıp ağ yapısı kuruyor. Metakrilatlar hassasiyet yapabilir, eldiven tak."),
            ("idea", "Çapraz bağ arttıkça jel daha sert olur ama daha az şişer."),
        ],
        "start": [("point", "İlk aşamada polimerizasyonu, ikinci aşamada suda şişmeyi izleyeceğiz.")],
        "progress": [
            (0.20, "idle_hand", "Dönüşüm eğrisi başta hızlı yükseliyor; serbest radikaller monomeri tüketiyor."),
            (0.45, "think", "Eğri yavaşlıyor; kalan monomer azaldıkça polimerizasyon hızı düşer."),
            (0.75, "idea", "Şişmeyi elastik ağ sınırlıyor: Flory–Rehner dengesi."),
        ],
        "swelling_start": [
            ("hold_flask", "Jel hazır, şimdi suya koydum. Şişme başlıyor!"),
            ("point", "Sağ alttaki eğri şişme oranı Q'yu gösteriyor."),
        ],
        "finish": [
            ("cheer", "Jel denge şişmesine ulaştı: Qₑ = {qeq:.2f}."),
            ("point", "Young modülü {E:.1f} kPa, çapraz bağlar arası Mc ≈ {mc:.0f} g/mol."),
            ("idea", "EGDMA oranını artırıp tekrar dene; sertlik artarken Qₑ düşecek."),
        ],
        "warn_low_conv": [("think", "Dönüşüm %50'nin altında kaldı; sağlam bir ağ oluşmamış olabilir. Polimerizasyon süresini veya başlatıcıyı artır.")],
    },

    # alanlar: eta, qh, qc, w
    "isi_makinesi": {
        "intro": [
            ("idle", "Merhaba! Carnot çevrimiyle ideal bir ısı makinesini inceleyeceğiz."),
            ("idea", "Çevrim iki izotermal ve iki adyabatik süreçten oluşuyor; iki sıcaklık arasında mümkün olan en yüksek verimi verir."),
            ("point", "Solda piston–silindir, sağda P–V diyagramı var."),
        ],
        "start": [("idle_hand", "Gazı sıcak rezervuarla temas ettirerek başlıyorum.")],
        "phase_0": [("point", "1→2 İzotermal genleşme: gaz sıcak rezervuardan Q_H ısısı alıyor, sıcaklık sabit.")],
        "phase_1": [("idea", "2→3 Adyabatik genleşme: ısı alışverişi yok, gaz genleşirken soğuyor.")],
        "phase_2": [("idle_hand", "3→4 İzotermal sıkışma: gaz soğuk rezervuara Q_C ısısı veriyor.")],
        "phase_3": [("think", "4→1 Adyabatik sıkışma: gaz ısınarak başlangıç haline dönüyor.")],
        "cycle_end": [
            ("cheer", "Bir çevrim tamamlandı!"),
            ("idea", "Çevrim başına net iş W = Q_H − Q_C."),
        ],
        "finish": [
            ("cheer", "Simülasyon bitti! Carnot verimi %{eta:.1f}."),
            ("point", "Çevrim başına Q_H = {qh:.1f} J, Q_C = {qc:.1f} J, W = {w:.1f} J."),
            ("idea", "η = 1 − T_C/T_H. Verimi artırmak için sıcaklık farkını büyütmelisin; %100 verim ancak T_C = 0 K ile mümkün."),
        ],
        "error_temp": [("think", "Soğuk rezervuarın sıcaklığı (T_C) sıcak rezervuardan (T_H) küçük olmalı, yoksa ısı makinesi çalışmaz.")],
    },

    # alanlar: formula, mw
    "elementel_analiz": {
        "intro": [
            ("idle", "Merhaba! CHN(S) elementel analiziyle bileşiğin formülünü doğrulayacağız."),
            ("hold_flask", "Numune kalay kapsülde yaklaşık 1000 °C'de O₂ ile yanıyor: C→CO₂, H→H₂O, N→N₂, S→SO₂."),
            ("idea", "Gazlar kolonda ayrılıp TCD dedektörüyle ölçülüyor. Kabul kriteri: sapma ≤ %0,3."),
        ],
        "start": [("point", "Kromatogramı izle; her gaz kendi piki ile gelecek.")],
        # pik zamanı (dk) / ilerleme: N₂ 1.2 / ~0.16, CO₂ 2.5 / ~0.33, H₂O 4.0 / ~0.53, SO₂ 6.0 / ~0.80
        # Sadece o elementin atom sayısı > 0 ise göster.
        "peak_N2": [("point", "İlk pik N₂: numunedeki azotun ölçüsü.")],
        "peak_CO2": [("point", "İkinci pik CO₂: karbon miktarını buradan hesaplıyoruz.")],
        "peak_H2O": [("point", "Üçüncü pik H₂O: hidrojen içeriği.")],
        "peak_SO2": [("point", "Son pik SO₂: bileşikte kükürt var demek.")],
        "finish_ok": [
            ("cheer", "Bileşik doğrulandı! Tüm sapmalar ≤ %0,3."),
            ("idea", "Formül {formula}, mol kütlesi {mw:.3f} g/mol."),
        ],
        "finish_fail": [
            ("think", "Kabul kriteri sağlanmadı; bazı elementlerde sapma %0,3'ün üstünde."),
            ("idea", "Numunenin saflığını kontrol et ya da analizi tekrarla. Cihaz hatasını düşürmek de işe yarar."),
        ],
        "error_none": [("think", "En az bir element için atom sayısı girmelisin.")],
        "error_no_c": [("think", "CHN analizi için bileşikte en az bir karbon atomu olmalı.")],
    },

    # alanlar: rs, rct, cdl, tau, fc, i0
    "impedimetri": {
        "intro": [
            ("idle", "Merhaba! Empedans spektroskopisiyle elektrot–çözelti arayüzünü inceleyeceğiz."),
            ("idea", "Sistemi Randles devresiyle modelliyoruz: Rs + (Cdl ∥ (Rct + Zw))."),
            ("hold_flask", "Hücrede [Fe(CN)₆]³⁻/⁴⁻ redoks çifti ve 0,1 M KCl var."),
        ],
        "start": [("point", "Frekansı yüksekten düşüğe tarıyorum. Nyquist grafiğinde noktalar soldan sağa dizilecek.")],
        "progress": [
            (0.10, "idle_hand", "Yüksek frekansta ilk nokta çözelti direncini, yani Rs'yi verir."),
            (0.50, "point", "Orta frekanslara geldik; yarım daire burada oluşuyor, çapı yük transfer direnci Rct."),
            (0.85, "think", "Düşük frekansta 45°'lik bir kuyruk başlıyor: difüzyon, yani Warburg empedansı."),
        ],
        "finish": [
            ("cheer", "Tarama bitti, verileri Randles devresine fit ettim!"),
            ("point", "Rs = {rs:.1f} Ω, Rct = {rct:.1f} Ω, Cdl = {cdl:.2f} µF."),
            ("idea", "τ = Rct·Cdl = {tau:.3g} s, karakteristik frekans {fc:.3g} Hz."),
            ("idle_hand", "Değişim akım yoğunluğu i₀ = {i0:.3g} A/cm². Rct küçüldükçe yük transferi hızlanır."),
        ],
        "error_freq": [("think", "Maksimum frekans minimum frekanstan büyük olmalı.")],
    },
}


class Zahira:
    """Bir deneyin konuşmalarını sprite etiketli satırlar olarak verir."""

    def __init__(self, exp_key):
        self.key = exp_key
        self.d = DIALOGUES[exp_key]

    def say(self, key, **fmt):
        """Anahtara ait tüm satırları [Line(sprite, text)] olarak döndürür."""
        return [Line(s, t.format(**fmt)) for s, t in self.d.get(key, [])]

    def progress(self, prev, now, **fmt):
        """İlerleme prev -> now aralığında eşiği geçen satırları döndürür."""
        out = []
        for thr, s, t in self.d.get("progress", []):
            if prev < thr <= now:
                out.append(Line(s, t.format(**fmt)))
        return out


def general(key):
    return [Line(s, t) for s, t in GENEL.get(key, [])]


# === KONUSMA-FIX-V1 ===
def _safe_fmt(text, fmt):
    try:
        return text.format(**fmt)
    except (KeyError, IndexError, ValueError):
        return None  # eksik alan: satırı atla, sunucuyu düşürme


def _say(self, key, **fmt):
    out = []
    for s, t in self.d.get(key, []):
        txt = _safe_fmt(t, fmt)
        if txt is not None:
            out.append(Line(s, txt))
    return out


def _progress(self, prev, now, **fmt):
    out = []
    for thr, s, t in self.d.get("progress", []):
        if prev < thr <= now:
            txt = _safe_fmt(t, fmt)
            if txt is not None:
                out.append(Line(s, txt))
    return out


Zahira.say = _say
Zahira.progress = _progress

# Kolon kromatografisi (adaptör Rs hesaplıyor; eski metinler İnce Tabaka/Rf idi)
DIALOGUES["kromatografi"] = {
    "intro": [
        ("idle", "Merhaba! Kolon kromatografisiyle iki bileşenli bir karışımı ayıracağız."),
        ("hold_flask", "Bileşenler sabit faz ile hareketli faz arasında paylaşılır. Sabit faza daha çok tutunan bileşen kolondan daha geç çıkar; buna alıkonma zamanı, tR, deriz."),
        ("idea", "Ayrımın ölçüsü çözünürlük: Rs = 2·(tR2 − tR1) / (w1 + w2). Rs ≥ 1,5 ise pikler taban çizgisine kadar ayrılmıştır."),
        ("idle_hand", "Pik genişliği plaka sayısı N ile belirlenir: σ = tR/√N. Plaka sayısı arttıkça pikler incelir, ayrım iyileşir."),
    ],
    "start": [("point", "Karışımı kolonun başına yükledim. Grafikte dedektör sinyalinin zamanla nasıl çizildiğini izle.")],
    "progress": [
        (0.25, "idle_hand", "Sabit faza en az tutunan bileşen kolondan ilk çıkar ve ilk pik oluşur."),
        (0.60, "think", "Sonra daha güçlü tutunan bileşen gelir. İki pik birbirine yakınsa örtüşme başlar."),
        (0.92, "point", "Sinyal taban çizgisine dönüyor, bileşenlerin hepsi kolondan çıktı."),
    ],
    "finish_good": [
        ("cheer", "Pikler tam ayrıldı! Çözünürlük Rs = {rs:.2f}."),
        ("idea", "Rs ≥ 1,5 olduğunda pikler taban çizgisine kadar ayrılır ve nicel analiz güvenilir olur."),
    ],
    "finish_overlap": [
        ("think", "Pikler kısmen örtüşüyor, Rs = {rs:.2f}."),
        ("idea", "Plaka sayısını artırmak ya da tR farkını büyütmek (örneğin hareketli fazı değiştirmek) çözünürlüğü yükseltir. Rs yaklaşık √N ile artar."),
    ],
}
