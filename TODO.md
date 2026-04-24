Högprio:
- Visa text och frys spelet när man vinner.
- Visa legal moves (med svag grön).
- När man skapar så bestämmer man cooldowns (behöver "Läs default pjäser från motor och presentera klienten (e.g. coolsdowns ska komma från GameState)")

Medelprio:
- Ny match (med nytt spel-id) med samma spelare
- Dragloggar enkelt tillgängliga (motor som exponeras i klient).

Lågprio:
- Lägg till gå med höger (utför giltigt drag och avmarkerar) _och_ vänster klick på ogiltiga drag avmarkerar, esc avmarkerar. (edited) 

Buggar:
- Kung kan ta pjäser under hot
- Kung kan bara rokadera om fel flank är fri
- Backend borde ej returnera 500 vid illeagal move (4xx)
