# -*- coding: utf-8 -*-
"""
Contenu & moteur de scoring de la grille de Due Diligence TBI (IMC).

Module PUR (aucune dépendance Streamlit) : il peut être importé et testé seul.
Source doctrinale : «الوجيز في القانون الدولي للاستثمار» — Pr F. Al Harchani,
Latrach Édition, 2026.
"""

# ---- Charte IMC ----
NAVY = "#1C2A4A"
TURQ = "#3DB9BC"
GOLD = "#C9A961"

# ---- Statuts (libellé -> points) ; N/A et "À évaluer" = exclus du calcul ----
FAV   = "🟢 Favorable"
WATCH = "🟡 À surveiller"
RISK  = "🔴 Risque"
NA    = "⚪ N/A"
TODO  = "— À évaluer"

STATUTS = [TODO, FAV, WATCH, RISK, NA]
POINTS = {FAV: 2, WATCH: 1, RISK: 0}   # TODO et NA absents => exclus


def points(statut):
    """Points d'un statut, ou None si non comptabilisé (À évaluer / N/A)."""
    return POINTS.get(statut)


# ---- Les 7 blocs / 44 critères : (réf, libellé, à vérifier, poids) ----
BLOCS = [
    ("A", "Investissement & investisseur", [
        ("A1", "Nationalité de l'investisseur clairement établie",
         "Personne physique : nationalité effective ; personne morale : critère de rattachement du TBI", 1),
        ("A2", "Critère de rattachement de la personne morale compatible avec le TBI",
         "Constitution / siège social réel / contrôle effectif — selon le texte", 2),
        ("A3", "Substance économique réelle dans l'État d'origine",
         "Anti treaty-shopping abusif : activité, bureaux, salariés (vs boîte aux lettres)", 1),
        ("A4", "Risque « Denial of Benefits » écarté",
         "Contrôle par ressortissant d'État tiers/sans TBI + absence d'activités substantielles", 2),
        ("A5", "Opération = « investissement » protégé (critères Salini)",
         "Apport financier/matériel, durée, risque, contribution au développement", 2),
        ("A6", "Forme de l'investissement couverte",
         "Liste d'actifs du TBI : IDE, titres, contrats, PI, concessions, prêts (déf. large/étroite)", 1),
        ("A7", "Investissement admis conformément au droit de l'État hôte",
         "Légalité à l'entrée : autorisations, secteur ouvert, absence de corruption", 2),
    ]),
    ("B", "Traité applicable & champ d'application", [
        ("B1", "Existence d'un TBI (ou chapitre invest. d'un ALE) origine–hôte",
         "Rechercher le traité bilatéral ou multilatéral applicable", 2),
        ("B2", "Traité signé ET entré en vigueur (ratifié)",
         "Un traité signé non ratifié ne protège pas", 2),
        ("B3", "Génération du traité identifiée",
         "Ancienne (large) vs nouvelle (précise, avec exceptions/obligations)", 1),
        ("B4", "Champ ratione materiae",
         "L'investissement entre dans la définition couverte par le traité", 1),
        ("B5", "Champ ratione temporis",
         "Couvre l'investissement : date critique, antériorité, différends préexistants", 2),
        ("B6", "Champ ratione loci",
         "Territoire couvert (y c. ZEE / plateau continental si pertinent)", 1),
        ("B7", "Clause de survie (sunset) en cas de dénonciation",
         "Durée de protection résiduelle après fin du traité", 1),
        ("B8", "Autres instruments mobilisables",
         "Via NPF, Convention CIRDI 1965, traités régionaux arabes, multilatéraux", 1),
    ]),
    ("C", "Standards de traitement", [
        ("C1", "Traitement national (TN)",
         "Égalité avec l'investisseur local — portée et exceptions", 1),
        ("C2", "Nation la plus favorisée (NPF)",
         "Portée : fond seulement, ou aussi règlement des différends ?", 1),
        ("C3", "Traitement juste et équitable (TJE/FET)",
         "Autonome ou rattaché au standard minimum coutumier ? Contenu précisé ?", 2),
        ("C4", "Protection et sécurité pleines et entières",
         "Protection physique et juridique de l'investissement", 1),
        ("C5", "Libre transfert des fonds",
         "Capital, revenus, dividendes, salaires — garantie de rapatriement", 2),
        ("C6", "Restrictions au transfert identifiées",
         "Balance des paiements, mesures prudentielles, contrôle des changes", 1),
        ("C7", "Interdiction des prescriptions de résultat",
         "Pas d'obligation de contenu local, export, transfert techno imposé", 1),
        ("C8", "Clause parapluie (umbrella)",
         "Les engagements contractuels de l'État sont-ils élevés au rang conventionnel ?", 1),
    ]),
    ("D", "Protection contre l'expropriation", [
        ("D1", "Clause d'expropriation couvrant direct ET indirect",
         "Nationalisation + mesures équivalentes (rampantes)", 2),
        ("D2", "Critères d'expropriation indirecte précisés",
         "Effet de la mesure, proportionnalité, but légitime", 2),
        ("D3", "« Droit de l'État à réguler » / annexe interprétative",
         "Mesures de bonne foi d'intérêt général non indemnisables (sauf exception)", 1),
        ("D4", "Conditions de licéité réunies",
         "Intérêt public, non-discrimination, légalité procédurale", 1),
        ("D5", "Standard d'indemnisation",
         "Prompte, adéquate, effective (valeur marchande — formule Hull)", 2),
    ]),
    ("E", "Garantie & risques non commerciaux", [
        ("E1", "Risques politiques cartographiés",
         "Expropriation, guerre/troubles, non-transfert, rupture de contrat", 2),
        ("E2", "Assurance risque politique souscrite ou disponible",
         "MIGA, ATI-ACA, agence nationale (COTUNACE), bailleurs", 1),
        ("E3", "Investissement éligible à la garantie",
         "Conditions d'éligibilité de l'organisme assureur", 1),
        ("E4", "Subrogation de l'assureur prévue",
         "Report des droits de l'investisseur vers l'assureur après indemnisation", 1),
    ]),
    ("F", "Règlement des différends (ISDS)", [
        ("F1", "Clause de règlement investisseur–État présente",
         "Accès de l'investisseur à un for international", 2),
        ("F2", "Consentement de l'État à l'arbitrage donné dans le traité",
         "Offre d'arbitrage permanente vs au cas par cas", 2),
        ("F3", "For identifié",
         "CIRDI/ICSID, CNUDCI ad hoc, CCI, Cour arabe de l'investissement", 1),
        ("F4", "Négociation amiable / cooling-off ; pas de fork-in-the-road piégeux",
         "Délai préalable à respecter ; choix de for définitif", 1),
        ("F5", "Épuisement des recours internes : exigé ou non ?",
         "Condition préalable éventuelle à l'arbitrage", 1),
        ("F6", "Loi applicable au fond déterminée",
         "Droit de l'État hôte, droit international, clauses du contrat", 1),
        ("F7", "Mécanismes nouvelle génération",
         "Cour permanente, médiation obligatoire, matières exclues de l'arbitrage", 1),
        ("F8", "Exécution de la sentence sécurisée",
         "Conv. New York 1958 / Conv. Washington 1965", 2),
    ]),
    ("G", "Obligations & conformité de l'investisseur", [
        ("G1", "Conformité anti-corruption",
         "Une entrée entachée de corruption peut faire perdre toute protection", 2),
        ("G2", "Dispositif LBC-FT",
         "Lutte anti-blanchiment et financement du terrorisme", 1),
        ("G3", "RSE / environnement / droits humains",
         "Obligations des traités de nouvelle génération", 1),
        ("G4", "Respect continu du droit local et des autorisations",
         "Conformité pendant toute la vie de l'investissement", 1),
    ]),
]

# ---- Référentiel (glossaire) ----
GLOSSAIRE = [
    ("TBI", "Traité bilatéral d'investissement : accord entre deux États pour protéger et promouvoir les investissements de leurs ressortissants."),
    ("Critères Salini", "Faisceau d'indices définissant un « investissement » protégé : apport, durée, risque et contribution au développement de l'État hôte."),
    ("Denial of Benefits", "Clause permettant à l'État de refuser la protection à une société sans activité réelle ou contrôlée par un ressortissant d'un État tiers."),
    ("Traitement national (TN)", "L'investisseur étranger n'est pas traité moins favorablement que l'investisseur local dans des situations comparables."),
    ("NPF", "Nation la plus favorisée : l'investisseur bénéficie du traitement le plus favorable accordé à tout investisseur d'un État tiers."),
    ("TJE / FET", "Traitement juste et équitable : standard central (bonne foi, transparence, protection des attentes légitimes, absence d'arbitraire)."),
    ("Clause parapluie", "Élève les engagements contractuels de l'État envers l'investisseur au rang d'obligations conventionnelles protégées par le traité."),
    ("Expropriation directe", "Transfert formel ou saisie de la propriété de l'investisseur par l'État (nationalisation)."),
    ("Expropriation indirecte", "Mesure étatique qui, sans transfert de titre, prive l'investisseur de la substance/jouissance de son bien (« mesure équivalente »)."),
    ("Droit de l'État à réguler", "Faculté reconnue à l'État de légiférer pour l'intérêt général (santé, environnement) ; les mesures de bonne foi non discriminatoires ne sont pas, en principe, une expropriation."),
    ("Formule Hull", "Standard d'indemnisation : « prompte, adéquate et effective » (valeur marchande de l'investissement)."),
    ("Prescriptions de résultat", "Obligations imposées à l'investisseur (contenu local, quotas d'export, transfert de technologie) ; souvent interdites."),
    ("ISDS", "Règlement des différends investisseur-État : mécanisme donnant à l'investisseur un accès direct à l'arbitrage international contre l'État hôte."),
    ("CIRDI / ICSID", "Centre international pour le règlement des différends relatifs aux investissements (Convention de Washington, 18 mars 1965) — principale institution d'arbitrage."),
    ("Subrogation", "Report, vers l'assureur qui a indemnisé l'investisseur, des droits de ce dernier contre l'État hôte."),
    ("Traité de nouvelle génération", "Traité récent plus précis : encadre les standards, consacre le droit de réguler, impose des obligations à l'investisseur, réforme l'arbitrage."),
    ("Clause de survie (sunset)", "Maintient la protection du traité pendant un délai après sa dénonciation (souvent 10–15 ans)."),
]


# ---- Moteur de scoring ----
def score_bloc(criteres, statuts_par_ref):
    """Retourne (score, max) pour un bloc. statuts_par_ref : {ref: statut}."""
    score = 0
    maxi = 0
    for ref, _lib, _chk, poids in criteres:
        p = points(statuts_par_ref.get(ref))
        if p is None:
            continue
        score += p * poids
        maxi += 2 * poids
    return score, maxi


def score_global(statuts_par_ref):
    """Retourne (score_total, max_total) sur l'ensemble des blocs."""
    s = m = 0
    for _code, _titre, criteres in BLOCS:
        bs, bm = score_bloc(criteres, statuts_par_ref)
        s += bs
        m += bm
    return s, m


def pourcentage(score, maxi):
    """Fraction 0..1, ou None si rien d'évalué."""
    return (score / maxi) if maxi else None


def verdict(pct):
    """(libellé, couleur_hex) selon le seuil. pct = fraction ou None."""
    if pct is None:
        return "À évaluer", "#7A8290"
    if pct >= 0.80:
        return "🟢 Bien protégé", "#2E7D32"
    if pct >= 0.60:
        return "🟡 Protection partielle — points à négocier", "#B8860B"
    return "🔴 Protection faible — risque élevé", "#C0392B"
