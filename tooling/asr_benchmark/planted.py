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
            (
                "Pendant les vacances, je suis visité ma famille.",
                "je suis visité",
                "j'ai rendu visite à",
            ),
            ("Ils ont devenu de très bons amis.", "ils ont devenu", "ils sont devenus"),
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
            ("Tu peux me donner le adresse de ton ami ?", "le adresse", "l'adresse"),
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
                "Je pense que c'est une bon idée de commencer tôt.",
                "une bon idée",
                "une bonne idée",
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
