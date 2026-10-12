# -*- coding: utf-8 -*-
"""
Contenu métier du Diagnostic Stratégique 360° IMC.
- PILLARS : 6 piliers, chacun avec ses questions (options scorées 0..100)
- recommend_services() : mappe les piliers faibles aux services IMC
- CATALOGUE : offres de services IMC (4 familles)
- ANNUAIRE : formules Starter / VIP
Devise : DT. Tarifs connus repris ; « sur devis » ailleurs (à compléter par Nizar).
"""

# Chaque question : (clé, libellé, [(label_option, score), ...])
# Les options vont du meilleur (100) au moins bon (0).
PILLARS = [
    {
        "key": "finance", "icon": "💶", "nom": "Gestion Financière & Comptabilité",
        "intro": "Marge, trésorerie, BFR, endettement, pilotage comptable.",
        "questions": [
            ("f1", "Connaissez-vous précisément votre marge brute ?",
             [("Oui, suivie chaque mois", 100), ("Approximativement", 50), ("Non, je ne la calcule pas", 0)]),
            ("f2", "Suivez-vous votre trésorerie ?",
             [("Oui, prévisionnel à jour", 100), ("De temps en temps", 50), ("Non", 0)]),
            ("f3", "Avez-vous un tableau de bord financier ?",
             [("Oui, mensuel", 100), ("Annuel seulement (bilan)", 50), ("Aucun", 0)]),
            ("f4", "Votre niveau d'endettement est-il maîtrisé ?",
             [("Oui, faible et choisi", 100), ("Modéré", 50), ("Élevé ou subi", 0)]),
            ("f5", "Vos bilans servent-ils à décider ?",
             [("Oui, analysés pour piloter", 100), ("Juste déposés", 50), ("Non exploités", 0)]),
        ],
    },
    {
        "key": "marketing", "icon": "📢", "nom": "Marketing & Référencement (SEO)",
        "intro": "Présence web, positionnement Google, conversion, contenu, acquisition.",
        "questions": [
            ("m1", "Disposez-vous d'un site web ?",
             [("Oui, optimisé et à jour", 100), ("Oui, mais ancien", 50), ("Non", 0)]),
            ("m2", "Votre visibilité sur Google (SEO) ?",
             [("1ʳᵉ page sur mes mots-clés", 100), ("Présent mais loin", 50), ("Invisible", 0)]),
            ("m3", "Votre site génère-t-il des demandes ?",
             [("Oui, régulièrement", 100), ("Rarement", 50), ("Non / pas de site", 0)]),
            ("m4", "Avez-vous une stratégie de contenu (blog, articles) ?",
             [("Oui, régulière", 100), ("Occasionnelle", 50), ("Aucune", 0)]),
            ("m5", "Pilotez-vous un budget d'acquisition (publicité) ?",
             [("Oui, avec ROI suivi", 100), ("Oui, sans suivi précis", 50), ("Aucun budget", 0)]),
        ],
    },
    {
        "key": "social", "icon": "📲", "nom": "Réseaux Sociaux & Image de Marque",
        "intro": "Animation des pages, engagement, régularité, identité visuelle, notoriété.",
        "questions": [
            ("s1", "Vos pages sociales (LinkedIn/Insta/FB/TikTok) sont-elles actives ?",
             [("Oui, plusieurs actives", 100), ("Une ou deux", 50), ("Aucune / abandonnées", 0)]),
            ("s2", "À quelle fréquence publiez-vous ?",
             [("Plusieurs fois par semaine", 100), ("De temps en temps", 50), ("Rarement", 0)]),
            ("s3", "Quel est votre niveau d'engagement (likes, messages) ?",
             [("Bon", 100), ("Faible", 50), ("Quasi nul", 0)]),
            ("s4", "Votre identité visuelle est-elle cohérente ?",
             [("Oui, charte pro", 100), ("Approximative", 50), ("Aucune", 0)]),
            ("s5", "Votre marque est-elle reconnue sur votre marché ?",
             [("Forte notoriété", 100), ("Moyenne", 50), ("Faible", 0)]),
        ],
    },
    {
        "key": "commercial", "icon": "💼", "nom": "Efficacité Commerciale & Ventes",
        "intro": "Prospection, pipeline, transformation des devis, CRM, fidélisation.",
        "questions": [
            ("c1", "Votre prospection est-elle structurée ?",
             [("Oui, systématique", 100), ("Informelle", 50), ("Aucune démarche", 0)]),
            ("c2", "Suivez-vous vos opportunités (pipeline) ?",
             [("Oui, CRM à jour", 100), ("Fichier Excel", 50), ("Rien de formalisé", 0)]),
            ("c3", "Connaissez-vous votre taux de transformation des devis ?",
             [("Oui, suivi", 100), ("Approximativement", 50), ("Inconnu", 0)]),
            ("c4", "Utilisez-vous un outil CRM ?",
             [("Oui", 100), ("Partiellement", 50), ("Non", 0)]),
            ("c5", "Avez-vous une démarche de fidélisation / réachat ?",
             [("Oui, programme actif", 100), ("Informelle", 50), ("Aucune", 0)]),
        ],
    },
    {
        "key": "rh", "icon": "👥", "nom": "Ressources Humaines & Organisation",
        "intro": "Climat, turnover, fiches de poste, recrutement, formation, délégation.",
        "questions": [
            ("h1", "Les fiches de poste sont-elles définies ?",
             [("Oui, claires", 100), ("Partiellement", 50), ("Non", 0)]),
            ("h2", "Votre processus de recrutement ?",
             [("Structuré", 100), ("Au cas par cas", 50), ("Aucun", 0)]),
            ("h3", "Climat social / turnover ?",
             [("Bon et stable", 100), ("Moyen", 50), ("Problématique", 0)]),
            ("h4", "Avez-vous un plan de formation ?",
             [("Oui", 100), ("Ponctuel", 50), ("Aucun", 0)]),
            ("h5", "La délégation / l'organisation est-elle claire ?",
             [("Oui, bien répartie", 100), ("Centralisée sur le dirigeant", 50), ("Désorganisée", 0)]),
        ],
    },
    {
        "key": "process", "icon": "⚙️", "nom": "Processus & Services Généraux",
        "intro": "Numérisation, conformité, gestion des contacts, structuration globale.",
        "questions": [
            ("p1", "Vos opérations sont-elles numérisées ?",
             [("Outils digitaux intégrés", 100), ("Partiellement", 50), ("Papier / manuel", 0)]),
            ("p2", "Votre conformité légale (contrats, données) ?",
             [("À jour", 100), ("Partielle", 50), ("Non maîtrisée", 0)]),
            ("p3", "Comment gérez-vous votre base de contacts / clients ?",
             [("Base structurée", 100), ("Éparpillée", 50), ("Aucune", 0)]),
            ("p4", "Vos procédures sont-elles documentées ?",
             [("Oui", 100), ("Quelques-unes", 50), ("Aucune", 0)]),
            ("p5", "Niveau de structuration global de l'entreprise ?",
             [("Très structuré", 100), ("Moyen", 50), ("Faible", 0)]),
        ],
    },
]

# Mapping pilier -> services IMC recommandés quand le pilier est faible (< 60 %).
PILLAR_SERVICES = {
    "finance":    ["Tableau de bord mensuel & gestion de trésorerie",
                   "Diagnostic financier & restructuration de dettes"],
    "marketing":  ["Audit & Stratégie SEO / Google My Business",
                   "Création de site web optimisé & campagnes d'acquisition"],
    "social":     ["Management complet des réseaux sociaux (contenu, visuels, planning)",
                   "Identité visuelle & branding"],
    "commercial": ["Mise en place de CRM & automatisation de la prospection",
                   "Structuration de l'équipe commerciale & scripts de vente"],
    "rh":         ["Recrutement sur-mesure & marque employeur",
                   "Optimisation organisationnelle"],
    "process":    ["Numérisation & structuration des process (CRM, base de données)",
                   "Référencement dans l'Annuaire Pro IMC"],
}

# Catalogue détaillé (familles -> offres). prix en DT ; None => « sur devis ».
CATALOGUE = [
    {"icon": "💶", "famille": "Comptabilité & Pilotage Financier", "offres": [
        ("Tableau de bord mensuel & gestion de trésorerie", "dès 300 DT / mois"),
        ("Diagnostic financier 360° & plan d'action", "1 200 – 1 800 DT"),
        ("Restructuration de dettes & dossier de financement", "2 000 – 3 500 DT"),
    ]},
    {"icon": "📢", "famille": "Marketing, SEO & Réseaux Sociaux", "offres": [
        ("Audit & Stratégie SEO / Google My Business", "sur devis"),
        ("Management complet des réseaux sociaux", "Essentiel 50 / Premium 150 / Élite 350 Dt /mois"),
        ("Campagne Sponsoring (Meta / Google Ads)", "dès 1 500 DT / mois"),
    ]},
    {"icon": "💼", "famille": "Développement Commercial & CRM", "offres": [
        ("Mise en place de CRM & automatisation de prospection", "sur devis"),
        ("Structuration équipe commerciale & scripts de vente", "sur devis"),
    ]},
    {"icon": "👥", "famille": "Conseil RH & Restructuration", "offres": [
        ("Recrutement sur-mesure & marque employeur", "sur devis"),
        ("Optimisation organisationnelle", "sur devis"),
    ]},
]

# Annuaire Pro IMC
ANNUAIRE = {
    "benefices": [
        "Backlink SEO de qualité vers votre site",
        "Visibilité B2B directe auprès de tout le réseau IMC",
        "Opportunités de synergies & partenariats",
        "Référencement dans un annuaire vérifié (crédibilité)",
    ],
    "formules": [
        ("Starter", "Gratuit / Inclus", ["Fiche entreprise de base", "Coordonnées & secteur",
                                         "Présence dans l'annuaire"]),
        ("VIP / Mise en avant", "sur devis / an", ["Badge Vérifié ✔", "Priorité dans les recherches de l'annuaire",
                                                    "Article de blog invité", "Mise en avant page d'accueil"]),
    ],
}

SECTEURS = ["Services", "Commerce / Négoce", "Industrie", "BTP / Construction", "Artisanat",
            "Santé", "Immobilier", "Restauration / Hôtellerie", "Tech / Digital", "Autre"]


def score_pillar(answers, pillar):
    """Moyenne des scores des réponses d'un pilier (0..100)."""
    vals = [answers.get(q[0], 50) for q in pillar["questions"]]
    return round(sum(vals) / len(vals)) if vals else 0


def compute_360(answers):
    """Renvoie {global, pillars:[{key,nom,icon,score}], faibles:[keys<60]}."""
    rows = []
    for p in PILLARS:
        sc = score_pillar(answers, p)
        rows.append({"key": p["key"], "nom": p["nom"], "icon": p["icon"], "score": sc})
    glob = round(sum(r["score"] for r in rows) / len(rows)) if rows else 0
    faibles = [r for r in rows if r["score"] < 60]
    return {"global": glob, "pillars": rows, "faibles": faibles}


def recommend_services(res360):
    """Liste de (pilier_nom, score, [services]) pour les piliers < 60 %, pire d'abord."""
    out = []
    for r in sorted(res360["pillars"], key=lambda x: x["score"]):
        if r["score"] < 60:
            out.append((r["nom"], r["icon"], r["score"], PILLAR_SERVICES.get(r["key"], [])))
    return out
