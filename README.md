# Révolution

Fiction. Une conversation de groupe entre quatre jeunes Franciliens, entrecoupée
de ce que le monde en dit (articles, dépêches, documents).

- `ebauche.md` : notes de travail (personnages, pistes, décisions).
- `rien-n-a-ete-vole.md` : toute première version, abandonnée, gardée pour mémoire.

## Lire

Ouvrir `index.html` dans un navigateur. La page est autonome : styles et
scripts sont embarqués, aucune dépendance réseau.

## Organisation

```
story/
  cast.json          personnages : nom et couleur (avatar à l'initiale)
  fr/
    book.json        titre, intro, membres du groupe, textes d'interface
    01-….txt         un fichier par séquence, lus dans l'ordre des noms
templates/           squelette HTML, CSS et JavaScript de la page
tools/build.py       story/ → index.html
```

`index.html` est **généré** : on ne l'édite jamais à la main. On modifie
`story/`, puis on régénère :

```bash
python3 tools/build.py
```

Le script signale toute erreur de saisie avec le fichier et la ligne
(personnage inconnu, heure mal formée, directive inconnue…).

Personne du groupe n'est « propriétaire » du téléphone : toutes les bulles sont
à gauche, chacune avec l'initiale et la couleur de son auteur.

## Écrire une séquence

Un fichier est une suite de blocs séparés par une ligne vide.

### Messages

```
rayan 09:12
Bien rentrés tout le monde ?
Nour t'as eu ton train finalement ?
```

- Première ligne : l'identifiant du personnage (voir `story/cast.json`) et l'heure.
- Lignes suivantes : le texte. Un retour à la ligne reste un retour à la ligne.
- `**gras**`, `*italique*`.
- `> texte` : citation (une réponse d'IA collée, un message transféré…).
- `[lien]`, `[photo]`, `[vidéo]`, `[capture d'écran]`, `[document]`,
  `[vocal 0:42]` seuls sur une ligne : pièce jointe.
- Un message fait uniquement d'émojis (trois au plus) s'affiche en grand,
  sans bulle. L'option `big` après l'heure force cet affichage.
- Typographie : tapez des espaces et apostrophes normales ; la génération pose
  les espaces insécables françaises et les apostrophes typographiques.
- `[reactions] 😂 2, ❤️ 1` en dernière ligne : réactions sous la bulle.
- Deux messages de suite du même auteur partagent l'avatar et le nom (sauf
  après une heure de silence).

### Articles et documents

```
[article] Fil d'actualité — 10:30
Titre de l'article
Premier paragraphe.
Deuxième paragraphe.
```

La première ligne donne la source, la deuxième le titre, les suivantes le corps
(un paragraphe par ligne).

### Directives

| directive | effet |
|-----------|-------|
| `[group] Maisonnée 7 🎸` | nom du groupe (le premier est obligatoire ; les suivants renomment le groupe dans l'en-tête au fil de la lecture) |
| `# Séquence 1 \| Le lendemain {#s1}` | début de séquence (titre, sous-titre, ancre facultative) |
| `--- Vendredi` | séparateur de date (`---` seul : courte pause dans la même journée) |
| `[event] Victor a renommé le groupe` | message système centré |
| `[interlude] Trois semaines plus tard` | ellipse centrée |
| `[spacer]` | grand blanc vertical |

## Conventions d'écriture du chat

- Pas de langage SMS, seulement quelques élisions à l'oral (« j'm'en fous », « t'as »).
- Dans un même message, pas de majuscule en début de ligne si la ligne
  précédente ne se termine pas par une ponctuation.
- On évite les messages multiples d'une même personne à la suite : quand ça
  arrive, c'est pour appuyer quelque chose ou parce qu'il y a un temps de
  réflexion.
- Rayan ne dit presque jamais de gros mots. Zoé écrit en minuscules.
