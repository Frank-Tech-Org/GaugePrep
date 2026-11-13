from dataclasses import dataclass


@dataclass(frozen=True)
class PlantedClip:
    id: str
    spoken: str
    error: str
    correct: str

    @property
    def reference(self) -> str:
        return self.spoken


# WHY: every error changes the sound, so only a recogniser that listens can keep it.
PLANTED_CLIPS: tuple[PlantedClip, ...] = tuple(
    PlantedClip(f"p{n:02d}", spoken, error, correct)
    for n, (spoken, error, correct) in enumerate(
        [
            ("Hier, j'ai allé au marché avec ma sœur.", "j'ai allé", "je suis allé"),
            (
                "Nous avons allé à Kribi pour les vacances.",
                "nous avons allé",
                "nous sommes allés",
            ),
            (
                "Elle a tombé dans l'escalier ce matin.",
                "elle a tombé",
                "elle est tombée",
            ),
            ("Hier soir, je suis mangé du poisson.", "je suis mangé", "j'ai mangé"),
            ("Elles ont parti hier soir.", "elles ont parti", "elles sont parties"),
            ("J'ai prendu le bus pour aller au travail.", "j'ai prendu", "j'ai pris"),
            (
                "Si j'aurais le temps, je viendrais avec toi.",
                "si j'aurais",
                "si j'avais",
            ),
            (
                "Si tu viendrais demain, on mangerait ensemble.",
                "si tu viendrais",
                "si tu venais",
            ),
            (
                "Il faut que je vais à la banque avant midi.",
                "que je vais",
                "que j'aille",
            ),
            (
                "Je voudrais que tu viens avec moi à Douala.",
                "que tu viens",
                "que tu viennes",
            ),
            ("Le maison de mes parents est près du marché.", "le maison", "la maison"),
            ("Ma sœur et moi, nous aimons le musique.", "le musique", "la musique"),
            ("Mon mère est professeur dans une école.", "mon mère", "ma mère"),
            ("Mon voiture est tombé en panne hier soir.", "mon voiture", "ma voiture"),
            ("Tu peux fermer le fenêtre, s'il te plaît ?", "le fenêtre", "la fenêtre"),
            (
                "Elle a une grand sœur qui habite à Paris.",
                "une grand sœur",
                "une grande sœur",
            ),
            (
                "Ils habitent dans un grande maison près de la gare.",
                "un grande maison",
                "une grande maison",
            ),
            (
                "C'est un belle journée pour se promener.",
                "un belle journée",
                "une belle journée",
            ),
            (
                "Nous cherchons un nouveau maison près du centre.",
                "un nouveau maison",
                "une nouvelle maison",
            ),
            (
                "Elle est gentil avec tous les enfants du quartier.",
                "elle est gentil",
                "elle est gentille",
            ),
            ("Je vais à le marché tous les samedis matin.", "à le marché", "au marché"),
            (
                "Elle a beaucoup des amis dans cette ville.",
                "beaucoup des amis",
                "beaucoup d'amis",
            ),
        ]
    )
)
