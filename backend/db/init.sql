-- Schéma de base de données ProcureAgent
-- Compatible PostgreSQL

DROP TABLE IF EXISTS journal_audit CASCADE;
DROP TABLE IF EXISTS lignes_commande CASCADE;
DROP TABLE IF EXISTS commandes CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS demandes CASCADE;
DROP TABLE IF EXISTS prix_catalogue CASCADE;
DROP TABLE IF EXISTS articles CASCADE;
DROP TABLE IF EXISTS fournisseurs CASCADE;
DROP TABLE IF EXISTS budgets CASCADE;
DROP TABLE IF EXISTS utilisateurs CASCADE;
DROP TABLE IF EXISTS services CASCADE;
DROP TABLE IF EXISTS regles CASCADE;

-- 1. Services & Utilisateurs (RBAC)
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    nom TEXT UNIQUE NOT NULL
);

CREATE TABLE utilisateurs (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    nom_complet TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('demandeur', 'acheteur', 'validateur')),
    service_id INT REFERENCES services(id) ON DELETE SET NULL
);

-- 2. Budgets annuels par service
CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    service_id INT NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    annee INT NOT NULL,
    montant_total NUMERIC(12,2) NOT NULL,
    montant_engage NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT uq_service_annee UNIQUE (service_id, annee)
);

-- 3. Fournisseurs & Articles au catalogue
CREATE TABLE fournisseurs (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    siret TEXT UNIQUE,
    autorise BOOLEAN NOT NULL DEFAULT TRUE,
    delai_jours INT DEFAULT 5
);

CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    reference TEXT UNIQUE NOT NULL,
    designation TEXT NOT NULL,
    categorie TEXT
);

CREATE TABLE prix_catalogue (
    fournisseur_id INT NOT NULL REFERENCES fournisseurs(id) ON DELETE CASCADE,
    article_id INT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    prix_unitaire NUMERIC(12,2) NOT NULL,
    PRIMARY KEY (fournisseur_id, article_id)
);

-- 4. Demandes et Documents (pièces jointes)
CREATE TABLE demandes (
    id UUID PRIMARY KEY,
    demandeur_id INT REFERENCES utilisateurs(id),
    service_id INT REFERENCES services(id),
    texte_brut TEXT NOT NULL,
    extraction JSONB,
    statut TEXT NOT NULL DEFAULT 'recue',
    cree_le TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    demande_id UUID REFERENCES demandes(id) ON DELETE CASCADE,
    nom_fichier TEXT NOT NULL,
    chemin TEXT NOT NULL,
    hash_sha256 TEXT UNIQUE NOT NULL,
    extraction JSONB,
    confiance_min NUMERIC(4,3),
    verifie_par TEXT,
    depose_le TIMESTAMPTZ DEFAULT now()
);

-- 5. Commandes d'achat et lignes de commande
CREATE TABLE commandes (
    id SERIAL PRIMARY KEY,
    demande_id UUID UNIQUE REFERENCES demandes(id),
    fournisseur_id INT NOT NULL REFERENCES fournisseurs(id),
    numero_po TEXT UNIQUE NOT NULL,
    montant_total NUMERIC(12,2) NOT NULL,
    approuve_par TEXT NOT NULL,
    cree_le TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE lignes_commande (
    id SERIAL PRIMARY KEY,
    commande_id INT NOT NULL REFERENCES commandes(id) ON DELETE CASCADE,
    article_id INT REFERENCES articles(id),
    designation TEXT NOT NULL,
    quantite INT NOT NULL CHECK (quantite > 0),
    prix_unitaire NUMERIC(12,2) NOT NULL
);

-- 6. Journal d'audit et règles de gestion
CREATE TABLE journal_audit (
    id BIGSERIAL PRIMARY KEY,
    demande_id UUID REFERENCES demandes(id) ON DELETE CASCADE,
    acteur TEXT NOT NULL,
    etape TEXT NOT NULL,
    decision TEXT,
    raison TEXT,
    donnees JSONB,
    ts TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE regles (
    cle TEXT PRIMARY KEY,
    valeur NUMERIC NOT NULL
);

-- ============================================================================
-- JEU D'ESSAI (SEED) RÉALISTE
-- ============================================================================

INSERT INTO regles (cle, valeur) VALUES 
('seuil_approbation', 1000.00),
('seuil_confiance_ocr', 0.85);

-- Services
INSERT INTO services (id, nom) VALUES 
(1, 'Design'),
(2, 'IT'),
(3, 'RH');

-- Utilisateurs avec rôles distincts
INSERT INTO utilisateurs (id, email, nom_complet, role, service_id) VALUES 
(1, 'alice.design@entreprise.com', 'Alice Martin', 'demandeur', 1),
(2, 'bob.acheteur@entreprise.com', 'Bob Acheteur', 'acheteur', 2),
(3, 'claire.manager@entreprise.com', 'Claire Valide', 'validateur', 1);

-- Budgets exercice 2026
-- Design : 50 000 total, 12 000 engagé -> reste 38 000 (Confortable)
-- IT     : 120 000 total, 95 000 engagé -> reste 25 000
-- RH     : 15 000 total, 14 200 engagé -> reste 800 (Tension / Test de dépassement)
INSERT INTO budgets (service_id, annee, montant_total, montant_engage) VALUES 
(1, 2026, 50000.00, 12000.00),
(2, 2026, 120000.00, 95000.00),
(3, 2026, 15000.00, 14200.00);

-- Fournisseurs
INSERT INTO fournisseurs (id, nom, siret, autorise, delai_jours) VALUES 
(1, 'Dell Entreprise', '11122233300010', TRUE, 5),
(2, 'LDLC Pro', '22233344400020', TRUE, 3),
(3, 'Buro+ Fournitures', '33344455500030', TRUE, 2),
(4, 'Vendeur Inconnu Market', '99988877700099', FALSE, 15);

-- Articles
INSERT INTO articles (id, reference, designation, categorie) VALUES 
(1, 'ECR-27-4K', 'Écran 27 pouces 4K', 'Informatique'),
(2, 'ECR-34-UW', 'Écran 34 pouces Ultrawide', 'Informatique'),
(3, 'CH-ERGO', 'Chaise de bureau ergonomique', 'Mobilier'),
(4, 'CLAV-LOGI', 'Clavier sans fil ergonomique', 'Périphérique');

-- Grille tarifaire catalogue
INSERT INTO prix_catalogue (fournisseur_id, article_id, prix_unitaire) VALUES 
(1, 1, 300.00),  -- Dell : Écran 27" à 300€
(2, 1, 290.00),  -- LDLC : Écran 27" à 290€
(1, 2, 650.00),  -- Dell : Écran 34" à 650€
(3, 3, 250.00),  -- Buro+ : Chaise à 250€
(2, 4, 85.00);   -- LDLC : Clavier à 85€

SELECT setval('services_id_seq', (SELECT MAX(id) FROM services));
SELECT setval('utilisateurs_id_seq', (SELECT MAX(id) FROM utilisateurs));
SELECT setval('fournisseurs_id_seq', (SELECT MAX(id) FROM fournisseurs));
SELECT setval('articles_id_seq', (SELECT MAX(id) FROM articles));
