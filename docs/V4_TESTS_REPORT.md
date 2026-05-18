# v4 — 211 GenAI Tests (OpenRouter + alle Phase-9-Fixes)

**Quelle:** `genai_results_v4.json`

## Zusammenfassung

| Metrik | Wert |
|---|---|
| Tests gesamt | **211** |
| ✓ Pass | **194** |
| ✗ Fail | 17 |
| 💥 Error | 0 |
| Pass-Rate | **91.9 %** |

## Pass-Rate pro Kategorie

| Kategorie | Pass | Fail | Error | Pass-Rate |
|---|---:|---:|---:|---:|
| liga | 45 | 0 | 0 | 100 % |
| saison_platz | 40 | 1 | 0 | 98 % |
| saison_punkte | 28 | 1 | 0 | 97 % |
| trainer | 22 | 0 | 0 | 100 % |
| spielergebnis | 20 | 0 | 0 | 100 % |
| playoff | 17 | 0 | 0 | 100 % |
| trend | 5 | 10 | 0 | 33 % |
| topscorer | 11 | 1 | 0 | 92 % |
| vergleich | 6 | 4 | 0 | 60 % |

## Einzelergebnisse

### ✓ `q_rank_2025_26` (saison_platz, 25.3s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2025/26?

**Erwartet:** `['5']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2025/26 auf dem 5. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2025/26';
```

---

### ✓ `q_rank_2024_25` (saison_platz, 18.2s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2024/25?

**Erwartet:** `['1']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2024/25 auf dem 1. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2024/25';
```

---

### ✓ `q_rank_2023_24` (saison_platz, 9.9s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2023/24?

**Erwartet:** `['2']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2023/24 auf dem 2. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2023/24';
```

---

### ✓ `q_rank_2022_23` (saison_platz, 14.2s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2022/23?

**Erwartet:** `['12']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2022/23 auf dem 12. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2022/23';
```

---

### ✓ `q_rank_2021_22` (saison_platz, 10.4s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2021/22?

**Erwartet:** `['6']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2021/22 auf dem 6. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2021/22';
```

---

### ✓ `q_rank_2020_21` (saison_platz, 23.3s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2020/21?

**Erwartet:** `['8']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2020/21 auf dem 8. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2020/21';
```

---

### ✓ `q_rank_2019_20` (saison_platz, 18.0s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2019/20?

**Erwartet:** `['4']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2019/20 auf dem 4. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2019/20';
```

---

### ✓ `q_rank_2018_19` (saison_platz, 9.3s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2018/19?

**Erwartet:** `['8']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2018/19 auf dem 8. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2018/19';
```

---

### ✓ `q_rank_2017_18` (saison_platz, 9.2s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2017/18?

**Erwartet:** `['9']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2017/18 auf dem 9. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2017/18';
```

---

### ✓ `q_rank_2016_17` (saison_platz, 8.5s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2016/17?

**Erwartet:** `['13']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2016/17 auf Tabellenplatz 13.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2016/17';
```

---

### ✓ `q_rank_2015_16` (saison_platz, 7.7s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2015/16?

**Erwartet:** `['14']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2015/16 auf Tabellenplatz 14.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2015/16';
```

---

### ✓ `q_rank_2014_15` (saison_platz, 10.9s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2014/15?

**Erwartet:** `['13']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2014/15 auf dem 13. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2014/15';
```

---

### ✓ `q_rank_2013_14` (saison_platz, 13.4s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2013/14?

**Erwartet:** `['12']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2013/14 auf dem 12. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2013/14';
```

---

### ✓ `q_rank_2012_13` (saison_platz, 10.3s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2012/13?

**Erwartet:** `['6']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2012/13 auf dem 6. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2012/13' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_rank_2011_12` (saison_platz, 10.7s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2011/12?

**Erwartet:** `['2']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2011/12 auf dem 2. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2011/12';
```

---

### ✓ `q_rank_2010_11` (saison_platz, 10.7s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2010/11?

**Erwartet:** `['2']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2010/11 auf dem 2. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2010/11';
```

---

### ✓ `q_rank_2009_10` (saison_platz, 14.6s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2009/10?

**Erwartet:** `['6']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2009/10 auf dem 6. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2009/10';
```

---

### ✓ `q_rank_2008_09` (saison_platz, 10.9s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2008/09?

**Erwartet:** `['4']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2008/09 auf dem 4. Tabellenplatz.

```sql
SELECT season, final_rank, points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2008/09';
```

---

### ✓ `q_rank_2007_08` (saison_platz, 18.3s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2007/08?

**Erwartet:** `['3']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2007/08 auf dem 3. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2007/08' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_rank_2006_07` (saison_platz, 14.5s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2006/07?

**Erwartet:** `['2']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2006/07 auf dem 2. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2006/07';
```

---

### ✓ `q_rank_2005_06` (saison_platz, 14.0s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2005/06?

**Erwartet:** `['6']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2005/06 auf dem 6. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2005/06';
```

---

### ✓ `q_rank_2004_05` (saison_platz, 55.8s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2004/05?

**Erwartet:** `['1']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2004/05 auf dem 1. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2004/05' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_rank_2003_04` (saison_platz, 23.2s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2003/04?

**Erwartet:** `['10']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2003/04 auf dem 10. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2003/04';
```

---

### ✗ `q_rank_2002_03` (saison_platz, 6.7s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2002/03?

**Erwartet:** `['5']`

**Antwort:** ⚠️  Konnte die Frage nicht beantworten (SQL-Fehler: {'code': '42601', 'details': None, 'hint': None, 'message': 'unterminated quoted string at or near "\') t"'}).

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2002/03' AND is_focus_team_season = TRUE'
```

**Fehlende Fakten:** `['5']`

---

### ✓ `q_rank_2001_02` (saison_platz, 20.3s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2001/02?

**Erwartet:** `['4']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2001/02 auf Tabellenplatz 4.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2001/02' LIMIT 1;
```

---

### ✓ `q_rank_2000_01` (saison_platz, 6.9s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 2000/01?

**Erwartet:** `['2']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 2000/01 auf dem 2. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2000/01';
```

---

### ✓ `q_rank_1999_00` (saison_platz, 10.4s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1999/00?

**Erwartet:** `['5']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1999/00 auf Tabellenplatz 5.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1999/00' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_rank_1998_99` (saison_platz, 7.8s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1998/99?

**Erwartet:** `['10']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1998/99 auf dem 10. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1998/99';
```

---

### ✓ `q_rank_1997_98` (saison_platz, 14.2s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1997/98?

**Erwartet:** `['1']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1997/98 auf dem 1. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1997/98';
```

---

### ✓ `q_rank_1996_97` (saison_platz, 9.1s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1996/97?

**Erwartet:** `['2']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1996/97 auf dem 2. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1996/97';
```

---

### ✓ `q_rank_1995_96` (saison_platz, 10.8s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1995/96?

**Erwartet:** `['3']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1995/96 auf dem 3. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1995/96';
```

---

### ✓ `q_rank_1994_95` (saison_platz, 9.1s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1994/95?

**Erwartet:** `['2']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1994/95 auf dem 2. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1994/95';
```

---

### ✓ `q_rank_1993_94` (saison_platz, 14.1s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1993/94?

**Erwartet:** `['1']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1993/94 auf dem 1. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1993/94';
```

---

### ✓ `q_rank_1992_93` (saison_platz, 10.1s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1992/93?

**Erwartet:** `['6']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1992/93 auf Tabellenplatz 6.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1992/93' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_rank_1991_92` (saison_platz, 12.8s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1991/92?

**Erwartet:** `['2']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1991/92 auf dem 2. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1991/92' AND is_focus_team_season = TRUE
```

---

### ✓ `q_rank_1990_91` (saison_platz, 9.0s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1990/91?

**Erwartet:** `['9']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1990/91 auf dem 9. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1990/91';
```

---

### ✓ `q_rank_1988_89` (saison_platz, 38.0s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1988/89?

**Erwartet:** `['4']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1988/89 auf dem 4. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1988/89';
```

---

### ✓ `q_rank_1987_88` (saison_platz, 20.6s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1987/88?

**Erwartet:** `['5']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1987/88 auf dem 5. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1987/88';
```

---

### ✓ `q_rank_1986_87` (saison_platz, 13.0s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1986/87?

**Erwartet:** `['2']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1986/87 auf dem 2. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1986/87';
```

---

### ✓ `q_rank_1985_86` (saison_platz, 19.1s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1985/86?

**Erwartet:** `['4']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1985/86 auf dem 4. Tabellenplatz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1985/86';
```

---

### ✓ `q_rank_1984_85` (saison_platz, 11.0s)

**Frage:** Auf welchem Tabellenplatz beendeten die Heilbronner Falken die Saison 1984/85?

**Erwartet:** `['3']`

**Antwort:** Die Heilbronner Falken beendeten die Saison 1984/85 auf Tabellenplatz 3.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1984/85';
```

---

### ✗ `q_pts_2025_26` (saison_punkte, 8.2s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2025/26?

**Erwartet:** `['93']`

**Antwort:** Keine Daten.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2025/26/27'
```

**Fehlende Fakten:** `['93']`

---

### ✓ `q_pts_2024_25` (saison_punkte, 12.5s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2024/25?

**Erwartet:** `['114']`

**Antwort:** Die Falken holten in der Saison 2024/25 114 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2024/25' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2023_24` (saison_punkte, 8.6s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2023/24?

**Erwartet:** `['109']`

**Antwort:** Die Falken holten in der Saison 2023/24 insgesamt 109 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2023/24' AND is_focus_team_season = TRUE
```

---

### ✓ `q_pts_2022_23` (saison_punkte, 9.3s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2022/23?

**Erwartet:** `['64']`

**Antwort:** Die Heilbronner Falken holten in der Saison 2022/23 64 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2022/23';
```

---

### ✓ `q_pts_2021_22` (saison_punkte, 10.9s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2021/22?

**Erwartet:** `['80']`

**Antwort:** Die Falken holten in der Saison 2021/22 80 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2021/22'
```

---

### ✓ `q_pts_2020_21` (saison_punkte, 10.3s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2020/21?

**Erwartet:** `['68']`

**Antwort:** Die Falken holten in der Saison 2020/21 68 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2020/21' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2019_20` (saison_punkte, 32.0s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2019/20?

**Erwartet:** `['84']`

**Antwort:** Die Falken holten in der Saison 2019/20 84 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2019/20';
```

---

### ✓ `q_pts_2018_19` (saison_punkte, 12.2s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2018/19?

**Erwartet:** `['74']`

**Antwort:** Die Falken holten in der Saison 2018/19 insgesamt 74 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2018/19' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2017_18` (saison_punkte, 19.9s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2017/18?

**Erwartet:** `['66']`

**Antwort:** Die Heilbronner Falken holten in der Saison 2017/18 66 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2017/18';
```

---

### ✓ `q_pts_2016_17` (saison_punkte, 18.4s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2016/17?

**Erwartet:** `['50']`

**Antwort:** Die Heilbronner Falken holten in der Saison 2016/17 50 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2016/17' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2015_16` (saison_punkte, 9.2s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2015/16?

**Erwartet:** `['36']`

**Antwort:** Die Heilbronner Falken holten in der Saison in der Saison 2015/16 36 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2015/16' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2014_15` (saison_punkte, 16.6s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2014/15?

**Erwartet:** `['34']`

**Antwort:** Die Falken holten in der Saison 2014/15 34 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2014/15' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2013_14` (saison_punkte, 20.8s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2013/14?

**Erwartet:** `['57']`

**Antwort:** Die Falken holten in der Saison 2013/14 57 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2013/14';
```

---

### ✓ `q_pts_2012_13` (saison_punkte, 22.6s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2012/13?

**Erwartet:** `['74']`

**Antwort:** Die Heilbronner Falken holten in der Saison 2012/13 74 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2012/13'
```

---

### ✓ `q_pts_2011_12` (saison_punkte, 11.8s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2011/12?

**Erwartet:** `['90']`

**Antwort:** Die Falken holten in der Saison 2011/12 90 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2011/12' AND is_focus_team_season = TRUE
```

---

### ✓ `q_pts_2010_11` (saison_punkte, 9.4s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2010/11?

**Erwartet:** `['93']`

**Antwort:** Die Heilbronner Falken holten in der Saison 2010/11 93 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2010/11';
```

---

### ✓ `q_pts_2009_10` (saison_punkte, 10.4s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2009/10?

**Erwartet:** `['86']`

**Antwort:** Die Falken holten in der Saison 2009/10 86 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2009/10' AND is_focus_team_season = TRUE
```

---

### ✓ `q_pts_2008_09` (saison_punkte, 16.0s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2008/09?

**Erwartet:** `['76']`

**Antwort:** Die Falken holten in der Saison 2008/09 76 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2008/09';
```

---

### ✓ `q_pts_2007_08` (saison_punkte, 7.8s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2007/08?

**Erwartet:** `['92']`

**Antwort:** Die Falken holten in der Saison 2007/08 92 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2007/08';
```

---

### ✓ `q_pts_2006_07` (saison_punkte, 15.3s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2006/07?

**Erwartet:** `['108']`

**Antwort:** Die Falken holten in der Saison 2006/07 108 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2006/07'
```

---

### ✓ `q_pts_2005_06` (saison_punkte, 9.1s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2005/06?

**Erwartet:** `['62']`

**Antwort:** Die Heilbronner Falken holten in der Saison 2005/06 insgesamt 62 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2005/06' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2004_05` (saison_punkte, 10.1s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2004/05?

**Erwartet:** `['82']`

**Antwort:** Die Falken holten in der Saison 2004/05 82 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2004/05' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2003_04` (saison_punkte, 10.5s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2003/04?

**Erwartet:** `['63']`

**Antwort:** Die Falken holten in der Saison 2003/04 63 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2003/04' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2002_03` (saison_punkte, 23.7s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2002/03?

**Erwartet:** `['97']`

**Antwort:** Die Falken holten in der Saison 2002/03 97 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2002/03' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_2001_02` (saison_punkte, 15.0s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2001/02?

**Erwartet:** `['92']`

**Antwort:** Die Heilbronner Falken holten in der Saison 2001/02 92 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2001/02' AND is_focus_team_season = TRUE
```

---

### ✓ `q_pts_2000_01` (saison_punkte, 17.7s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 2000/01?

**Erwartet:** `['86']`

**Antwort:** Die Falken holten in der Saison 2000/01 86 Punkte.

```sql
SELECT points FROM season_standings season_standings WHERE team = 'Heilbronner Falken' AND season = '2000/01' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_1999_00` (saison_punkte, 19.6s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 1999/00?

**Erwartet:** `['45']`

**Antwort:** Die Heilbronner Falken holten in der Saison 1999/00 45 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1999/00';
```

---

### ✓ `q_pts_1998_99` (saison_punkte, 11.6s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 1998/99?

**Erwartet:** `['62']`

**Antwort:** Die Falken holten in der Saison 1998/99 62 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1998/99' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_pts_1997_98` (saison_punkte, 15.8s)

**Frage:** Wie viele Punkte holten die Falken in der Saison 1997/98?

**Erwartet:** `['62']`

**Antwort:** Die Falken holten in der Saison 1997/98 62 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1997/98' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_top_2013_14` (topscorer, 22.4s)

**Frage:** Wer war Topscorer der Falken in der Saison 2013/14?

**Erwartet:** `['Robert Hock']`

**Antwort:** Topscorer der Heilbronner Falken in der Saison 2013/14 war Robert Hock mit 55 Punkten (11 Tore und 44 Assists).

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2013/14' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✓ `q_top_2014_15` (topscorer, 10.2s)

**Frage:** Wer war Topscorer der Falken in der Saison 2014/15?

**Erwartet:** `['Dustin Cameron']`

**Antwort:** Der Topscorer der Falken in der Saison 2014/15 war Dustin Cameron mit 50 Punkten (19 Tore, 31 Assists).

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2014/15' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✓ `q_top_2015_16` (topscorer, 28.4s)

**Frage:** Wer war Topscorer der Falken in der Saison 2015/16?

**Erwartet:** `['Adam Brace']`

**Antwort:** Adam Brace war mit 63 Punkten (28 Tore, 35 Assists) der Topscorer der Heilbronner Falken in der Saison 2015/16.

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2015/16' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✓ `q_top_2016_17` (topscorer, 25.8s)

**Frage:** Wer war Topscorer der Falken in der Saison 2016/17?

**Erwartet:** `['Rylan Schwartz']`

**Antwort:** Rylan Schwartz war mit 49 Punkten (17 Tore, 32 Assists) der Topscorer der Falken in der Saison 2016/17.

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2016/17' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✓ `q_top_2017_18` (topscorer, 12.5s)

**Frage:** Wer war Topscorer der Falken in der Saison 2017/18?

**Erwartet:** `['Brandon Alderson']`

**Antwort:** Der Topscorer der Heilbronner Falken in der Saison 2017/18 war Brandon Alderson mit 54 Punkten (25 Tore, 29 Assists).

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2017/18' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✓ `q_top_2018_19` (topscorer, 9.7s)

**Frage:** Wer war Topscorer der Falken in der Saison 2018/19?

**Erwartet:** `['Roope Ranta']`

**Antwort:** Der Topscorer der Heilbronner Falken in der Saison 2018/19 war Roope Ranta mit 79 Punkten (31 Tore und 48 Assists).

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2018/19' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✓ `q_top_2019_20` (topscorer, 18.5s)

**Frage:** Wer war Topscorer der Falken in der Saison 2019/20?

**Erwartet:** `['Dylan Wruck']`

**Antwort:** Dylan Wruck war mit 88 Punkten (24 Tore, 64 Assists) der Topscorer der Falken in der Saison 2019/20.

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2019/20' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✓ `q_top_2020_21` (topscorer, 14.5s)

**Frage:** Wer war Topscorer der Falken in der Saison 2020/21?

**Erwartet:** `['Dylan Wruck']`

**Antwort:** Der Topscorer der Heilbronner Falken in der Saison 2020/21 war Dylan Wruck mit 78 Punkten (23 Tore und 55 Assists).

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2020/21' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✓ `q_top_2021_22` (topscorer, 7.2s)

**Frage:** Wer war Topscorer der Falken in der Saison 2021/22?

**Erwartet:** `['Jeremy Williams']`

**Antwort:** Jeremy Williams war mit 62 Punkten (26 Tore, 36 Assists) Topscorer der Heilbronner Falken in der Saison 2021/22.

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2021/22' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✓ `q_top_2022_23` (topscorer, 7.0s)

**Frage:** Wer war Topscorer der Falken in der Saison 2022/23?

**Erwartet:** `['Alex Tonge']`

**Antwort:** Alex Tonge war mit 59 Punkten (19 Tore, 40 Assists) der Topscorer der Falken in der Saison 2022/23.

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2022/23' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---

### ✗ `q_top_2023_24` (topscorer, 17.6s)

**Frage:** Wer war Topscorer der Falken in der Saison 2023/24?

**Erwartet:** `['Pontus Wernerson Libäck']`

**Antwort:** Es liegen keine Daten vor.

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2023/24/25' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

**Fehlende Fakten:** `['Pontus Wernerson Libäck']`

---

### ✓ `q_top_2024_25` (topscorer, 7.1s)

**Frage:** Wer war Topscorer der Falken in der Saison 2024/25?

**Erwartet:** `['Nolan Ritchie']`

**Antwort:** Nolan Ritchie war mit 84 Punkten (38 Tore, 46 Assists) Topscorer der Falken in der Saison 2024/25.

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2024/25' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 5;
```

---

### ✓ `q_coach_2023_24_Petrozza` (trainer, 12.7s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2023/24?

**Erwartet:** `['Francesco Petrozza']`

**Antwort:** Francesco Petrozza war in der Saison 2023/24 als Headcoach der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2023/24' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2022_23_Morgan` (trainer, 10.5s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2022/23?

**Erwartet:** `['Jason Morgan']`

**Antwort:** In der Saison 2022/23 waren Jason Morgan und Martin Jiranek als Headcoaches der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2022/23' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2022_23_Jiranek` (trainer, 19.3s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2022/23?

**Erwartet:** `['Martin Jiranek']`

**Antwort:** In der Saison 2022/23 waren Jason Morgan und Martin Jiranek als Headcoaches der Heilbronner Falken tätig, beide vom 1. September 2022 bis zum 31. Mai 2023.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2022/23' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2021_22_Morgan` (trainer, 13.6s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2021/22?

**Erwartet:** `['Jason Morgan']`

**Antwort:** Jason Morgan war in der Saison 2021/22 als Headcoach der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2021/22' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2020_21_Zeiter` (trainer, 20.6s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2020/21?

**Erwartet:** `['Michel Zeiter']`

**Antwort:** Die Trainer der Heilbronner Falken in der Saison 2020/21 waren Michel Zeiter und William-Bill Stewart, beide als Headcoach vom 1. September 2020 bis zum 31. Mai 2021.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2020/21' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2020_21_Stewart` (trainer, 15.6s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2020/21?

**Erwartet:** `['William-Bill Stewart']`

**Antwort:** In der Saison 2020/21 waren Michel Zeiter und William-Bill Stewart als Headcoach der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2020/21' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2019_20_Mellitzer` (trainer, 14.8s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2019/20?

**Erwartet:** `['Alexander Mellitzer']`

**Antwort:** Alexander Mellitzer war in der Saison 2019/20 als Headcoach der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2019/20' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2018_19_Mellitzer` (trainer, 10.0s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2018/19?

**Erwartet:** `['Alexander Mellitzer']`

**Antwort:** Alexander Mellitzer war in der Saison 2018/19 als Headcoach der Heilbronner Falken tätig (vom 1. September 2018 bis 31. Mai 2019) tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2018/19' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2017_18_Unterluggauer` (trainer, 34.7s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2017/18?

**Erwartet:** `['Gerhard Unterluggauer']`

**Antwort:** Der Trainer der Heilbronner Falken in der Saison 2017/18 war Gerhard Unterluggauer.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2017/18' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2016_17_Dahlem` (trainer, 24.2s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2016/17?

**Erwartet:** `['Fabian Dahlem']`

**Antwort:** Fabian Dahlem war in der Saison 2016/17 Headcoach der Heilbronner Falken (vom 1. September 2016 bis 31. Mai 2017).

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2016/17' AND ct.role = 'Headcoach' ORDER BY ct.start_date LIMIT 1;
```

---

### ✓ `q_coach_2016_17_Unterluggauer` (trainer, 22.9s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2016/17?

**Erwartet:** `['Gerhard Unterluggauer']`

**Antwort:** Die Trainer der Heilbronner Falken in der Saison 2016/17 waren Fabian Dahlem und Gerhard Unterluggauer.

```sql
SELECT c.name AS coach_name FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2016/17' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2015_16_Dahlem` (trainer, 13.7s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2015/16?

**Erwartet:** `['Fabian Dahlem']`

**Antwort:** In der Saison 2015/16 waren Manfred Wolf und Fabian Dahlem als Headcoaches der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2015/16' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2015_16_Wolf` (trainer, 11.6s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2015/16?

**Erwartet:** `['Manfred Wolf']`

**Antwort:** In der Saison 2015/16 waren Manfred Wolf und Fabian Dahlem als Headcoaches der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2015/16' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2014_15_Wittmann` (trainer, 24.7s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2014/15?

**Erwartet:** `['Gerd Wittmann']`

**Antwort:** In der Saison 2014/15 waren Igors Pavlovs, Gerd Wittmann und Luigi Calce sr. als Headcoach der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2014/15' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2014_15_Pavlovs` (trainer, 15.4s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2014/15?

**Erwartet:** `['Igors Pavlovs']`

**Antwort:** In der Saison 2014/15 waren Igors Pavlovs, Gerd Wittmann und Luigi Calce sr. als Headcoaches der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2014/15' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2014_15_sr.` (trainer, 24.9s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2014/15?

**Erwartet:** `['Luigi Calce sr.']`

**Antwort:** In der Saison 2014/15 waren Igors Pavlovs, Gerd Wittmann und Luigi Calce sr. als Headcoaches der Heilbronner Falken tätig.

```sql
SELECT c.name AS coach_name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2014/15' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2013_14_Wittmann` (trainer, 22.0s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2013/14?

**Erwartet:** `['Gerd Wittmann']`

**Antwort:** Die Trainer der Heilbronner Falken in der Saison 2013/14 waren Kenneth Latta, Gerd Wittmann und Igors Pavlovs.

```sql
SELECT c.name FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2013/14' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2013_14_Pavlovs` (trainer, 11.0s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2013/14?

**Erwartet:** `['Igors Pavlovs']`

**Antwort:** Die Trainer der Heilbronner Falken in der Saison 2013/14 waren Kenneth Latta, Gerd Wittmann und Igors Pavlovs als Headcoaches.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2013/14' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2013_14_Latta` (trainer, 11.8s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2013/14?

**Erwartet:** `['Kenneth Latta']`

**Antwort:** In der Saison 2013/14 waren Kenneth Latta, Gerd Wittmann und Igors Pavlovs als Headcoaches der Heilbronner Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2013/14' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2012_13_sr.` (trainer, 20.6s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2012/13?

**Erwartet:** `['Rico Rossi sr.']`

**Antwort:** Rico Rossi sr. war in der Saison 2012/13 Headcoach der Heilbronner Falken (vom 1. September 2012 bis 31. Mai 2013).

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2012/13' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2011_12_sr.` (trainer, 16.2s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2011/12?

**Erwartet:** `['Rico Rossi sr.']`

**Antwort:** Der Trainer der Heilbronner Falken in der Saison 2011/12 war Rico Rossi sr.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2011/12' AND ct.role = 'Headcoach';
```

---

### ✓ `q_coach_2010_11_sr.` (trainer, 19.7s)

**Frage:** Wer war Trainer der Heilbronner Falken in der Saison 2010/11?

**Erwartet:** `['Rico Rossi sr.']`

**Antwort:** Der Trainer der Heilbronner Falken in der Saison 2010/11 war Rico Rossi sr.

```sql
SELECT c.name FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2010/11' AND ct.role = 'Headcoach';
```

---

### ✓ `q_league_2025_26` (liga, 33.1s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2025/26?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2025/26 in der Oberliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2025/26' LIMIT 1;
```

---

### ✓ `q_league_2024_25` (liga, 35.9s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2024/25?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2024/25 in der Oberliga Süd.

```sql
SELECT DISTINCT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2024/25'
```

---

### ✓ `q_league_2023_24` (liga, 12.6s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2023/24?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2023/24 in der Oberliga Süd.

```sql
SELECT DISTINCT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2023/24';
```

---

### ✓ `q_league_2022_23` (liga, 11.3s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2022/23?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2022/23 in der DEL2.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2022/23' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_league_2021_22` (liga, 9.5s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2021/22?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2021/22 in der DEL2.

```sql
SELECT DISTINCT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2021/22';
```

---

### ✓ `q_league_2020_21` (liga, 8.7s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2020/21?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2020/21 in der DEL2.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2020/21' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_league_2019_20` (liga, 8.3s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2019/20?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2019/20 in der DEL2.

```sql
SELECT DISTINCT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2019/20'
```

---

### ✓ `q_league_2018_19` (liga, 20.5s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2018/19?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2018/19 in der DEL2.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2018/19'
```

---

### ✓ `q_league_2017_18` (liga, 9.5s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2017/18?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2017/18 in der DEL2.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2017/18';
```

---

### ✓ `q_league_2016_17` (liga, 8.7s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2016/17?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2016/17 in der DEL2.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2016/17' LIMIT 1;
```

---

### ✓ `q_league_2015_16` (liga, 61.3s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2015/16?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2015/16 in der DEL2.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2015/16';
```

---

### ✓ `q_league_2014_15` (liga, 12.6s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2014/15?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2014/15 in der DEL2.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2014/15';
```

---

### ✓ `q_league_2013_14` (liga, 12.9s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2013/14?

**Erwartet:** `['DEL2']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2013/14 in der DEL2.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2013/14' AND is_focus_team_season = TRUE
```

---

### ✓ `q_league_2012_13` (liga, 7.5s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2012/13?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2012/13 in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2012/13';
```

---

### ✓ `q_league_2011_12` (liga, 10.0s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2011/12?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2011/12 in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2011/12' AND is_focus_team_season = TRUE LIMIT 1;
```

---

### ✓ `q_league_2010_11` (liga, 32.8s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2010/11?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2010/11 in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2010/11' LIMIT 1;
```

---

### ✓ `q_league_2009_10` (liga, 14.0s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2009/10?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2009/10 in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2009/10' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_league_2008_09` (liga, 33.4s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2008/09?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2008/09 in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2008/09' LIMIT 1;
```

---

### ✓ `q_league_2007_08` (liga, 12.3s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2007/08?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** In der Saison 2007/08 spielten die Heilbronner Falken in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2007/08';
```

---

### ✓ `q_league_2006_07` (liga, 5.9s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2006/07?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2006/07 in der Oberliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2006/07' LIMIT 1;
```

---

### ✓ `q_league_2005_06` (liga, 22.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2005/06?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2005/06 in der Oberliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2005/06';
```

---

### ✓ `q_league_2004_05` (liga, 13.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2004/05?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2004/05 in der Oberliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2004/05';
```

---

### ✓ `q_league_2003_04` (liga, 15.7s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2003/04?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** In der Saison 2003/04 spielten die Heilbronner Falken in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2003/04';
```

---

### ✓ `q_league_2002_03` (liga, 20.4s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2002/03?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2002/03 in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2002/03' AND is_focus_team_season = TRUE LIMIT 1;
```

---

### ✓ `q_league_2001_02` (liga, 18.0s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2001/02?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 2001/02 in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2001/02' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_league_2000_01` (liga, 11.1s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 2000/01?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** In der Saison 2000/01 spielten die Heilbronner Falken in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2000/01' AND is_focus_team_season = TRUE
```

---

### ✓ `q_league_1999_00` (liga, 10.0s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1999/00?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1999/00 in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1999/00' AND is_focus_team_season = TRUE LIMIT 1;
```

---

### ✓ `q_league_1998_99` (liga, 13.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1998/99?

**Erwartet:** `['2. Bundesliga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1998/99 in der 2. Bundesliga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1998/99';
```

---

### ✓ `q_league_1997_98` (liga, 14.5s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1997/98?

**Erwartet:** `['Hockey Premier League']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1997/98 in der Hockey Premier League.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1997/98'
```

---

### ✓ `q_league_1996_97` (liga, 27.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1996/97?

**Erwartet:** `['Hockey Premier League']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1996/97 in der Hockey Premier League.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1996/97' AND is_focus_team_season = TRUE LIMIT 1;
```

---

### ✓ `q_league_1995_96` (liga, 11.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1995/96?

**Erwartet:** `['Hockey Premier League']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1995/96 in der Hockey Premier League.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1995/96'
```

---

### ✓ `q_league_1994_95` (liga, 9.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1994/95?

**Erwartet:** `['1. Bundesliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1994/95 in der 1. Bundesliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1994/95' LIMIT 1;
```

---

### ✓ `q_league_1993_94` (liga, 13.3s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1993/94?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1993/94 in der Oberliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1993/94' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_league_1992_93` (liga, 29.0s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1992/93?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1992/93 in der Oberliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1992/93' AND is_focus_team_season = TRUE
```

---

### ✓ `q_league_1991_92` (liga, 20.8s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1991/92?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** In der Saison 1991/92 spielten die Heilbronner Falken in der Oberliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1991/92' LIMIT 1;
```

---

### ✓ `q_league_1990_91` (liga, 10.4s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1990/91?

**Erwartet:** `['Oberliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1990/91 in der Oberliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1990/91';
```

---

### ✓ `q_league_1988_89` (liga, 10.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1988/89?

**Erwartet:** `['2. Bundesliga Süd']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1988/89 in der 2. Bundesliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1988/89';
```

---

### ✓ `q_league_1987_88` (liga, 12.4s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1987/88?

**Erwartet:** `['2. Bundesliga Süd']`

**Antwort:** In der Saison 1987/88 spielten die Heilbronner Falken in der 2. Bundesliga Süd.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1987/88';
```

---

### ✓ `q_league_1986_87` (liga, 8.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1986/87?

**Erwartet:** `['Oberliga Nord']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1986/87 in der Oberliga Nord.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1986/87' LIMIT 1;
```

---

### ✓ `q_league_1985_86` (liga, 9.3s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1985/86?

**Erwartet:** `['Oberliga Mitte']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1985/86 in der Oberliga Mitte.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1985/86' AND is_focus_team_season = TRUE
```

---

### ✓ `q_league_1984_85` (liga, 11.3s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1984/85?

**Erwartet:** `['Regionalliga Süd-West']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1984/85 in der Regionalliga Süd-West.

```sql
SELECT DISTINCT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1984/85';
```

---

### ✓ `q_league_1983_84` (liga, 30.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1983/84?

**Erwartet:** `['Baden-Württemberg-Liga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1983/84 in der Baden-Württemberg-Liga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1983/84';
```

---

### ✓ `q_league_1982_83` (liga, 12.6s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1982/83?

**Erwartet:** `['Baden-Württemberg-Liga']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1982/83 in der Baden-Württemberg-Liga.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1982/83' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_league_1981_82` (liga, 33.6s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1981/82?

**Erwartet:** `['Landesliga BaWü']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1981/82 in der Landesliga BaWü.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1981/82' LIMIT 1;
```

---

### ✓ `q_league_1980_81` (liga, 25.2s)

**Frage:** In welcher Liga spielten die Heilbronner Falken in der Saison 1980/81?

**Erwartet:** `['Landesliga BaWü']`

**Antwort:** Die Heilbronner Falken spielten in der Saison 1980/81 in der Landesliga BaWü.

```sql
SELECT league FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '1980/81';
```

---

### ✓ `q_game_20260227` (spielergebnis, 11.4s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen ECDC Memmingen Indians und Heilbronner Falken am 2026-02-27?

**Erwartet:** `['7:2', '7-2', '7 zu 2']`

**Antwort:** Das Spiel zwischen ECDC Memmingen Indians und Heilbronner Falken am 2026-02-27 endete 7:2 für die Heimmannschaft.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2026-02-27' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('ECDC Memmingen Indians' IN (ht.name, at.name));
```

---

### ✓ `q_game_20260222` (spielergebnis, 10.5s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und Erding Gladiators am 2026-02-22?

**Erwartet:** `['2:7', '2-7', '2 zu 7']`

**Antwort:** Das Spiel zwischen den Heilbronner Falken und den Erding Gladiators am 2026-02-22 endete mit einem Ergebnis von Heilbronner Falken 2:7 Erding Gladiators.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2026-02-22' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Erding Gladiators' IN (ht.name, at.name));
```

---

### ✓ `q_game_20260220` (spielergebnis, 97.7s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen EHF Passau Black Hawks und Heilbronner Falken am 2026-02-20?

**Erwartet:** `['8:3', '8-3', '8 zu 3']`

**Antwort:** Das Spiel zwischen EHF Passau Black Hawks und Heilbronner Falken am 2026-02-20 endete mit 8:3 für die EHF Passau Black Hawks.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2026-02-20' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('EHF Passau Black Hawks' IN (ht.name, at.name));
```

---

### ✓ `q_game_20260206` (spielergebnis, 9.7s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und Bayreuth Tigers am 2026-02-06?

**Erwartet:** `['11:3', '11-3', '11 zu 3']`

**Antwort:** Das Spiel zwischen den Heilbronner Falken und den Bayreuth Tigers am 2026-02-06 endete 11:3 für die Heilbronner Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2026-02-06' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Bayreuth Tigers' IN (ht.name, at.name));
```

---

### ✓ `q_game_20260130` (spielergebnis, 39.5s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und Stuttgart Rebels am 2026-01-30?

**Erwartet:** `['2:7', '2-7', '2 zu 7']`

**Antwort:** Das Spiel zwischen den Heilbronner Falken und den Stuttgart Rebels am 2026-01-30 endete mit einem Ergebnis von Heilbronner Falken 2:7 Stuttgart Rebels.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2026-01-30' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Stuttgart Rebels' IN (ht.name, at.name));
```

---

### ✓ `q_game_20260120` (spielergebnis, 15.1s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Deggendorfer SC und Heilbronner Falken am 2026-01-20?

**Erwartet:** `['8:2', '8-2', '8 zu 2']`

**Antwort:** Das Spiel zwischen Deggendorfer SC und Heilbronner Falken am 2026-01-20 endete mit Deggendorfer SC 8:2 Heilbronner Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2026-01-20' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Deggendorfer SC' IN (ht.name, at.name));
```

---

### ✓ `q_game_20260116` (spielergebnis, 12.7s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen SC Riessersee und Heilbronner Falken am 2026-01-16?

**Erwartet:** `['0:6', '0-6', '0 zu 6']`

**Antwort:** Das Spiel zwischen SC Riessersee und Heilbronner Falken am 2026-01-16 endete mit einem Ergebnis von SC Riessersee 0:6 Heilbronner Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2026-01-16' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('SC Riessersee' IN (ht.name, at.name));
```

---

### ✓ `q_game_20260102` (spielergebnis, 23.2s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und EV Füssen am 2026-01-02?

**Erwartet:** `['6:2', '6-2', '6 zu 2']`

**Antwort:** Das Spiel am 2026-01-02 endete mit 6:2 für die Heilbronner Falken gegen den EV Füssen.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2026-01-02'   AND ('Heilbronner Falken' IN (ht.name, at.name))   AND ('EV Füssen' IN (ht.name, at.name));
```

---

### ✓ `q_game_20251228` (spielergebnis, 33.2s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Stuttgart Rebels und Heilbronner Falken am 2025-12-28?

**Erwartet:** `['1:7', '1-7', '1 zu 7']`

**Antwort:** Das Spiel zwischen den Stuttgart Rebels und den Heilbronner Falken am 2025-12-28 endete mit einem Ergebnis von Stuttgart Rebels 1:7 Heilbronner Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-12-28' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Stuttgart Rebels' IN (ht.name, at.name));
```

---

### ✓ `q_game_20251128` (spielergebnis, 11.1s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und Stuttgart Rebels am 2025-11-28?

**Erwartet:** `['8:2', '8-2', '8 zu 2']`

**Antwort:** Das Spiel zwischen den Heilbronner Falken und den Stuttgart Rebels am 2025-11-28 endete 8:2 für die Heilbronner Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-11-28' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Stuttgart Rebels' IN (ht.name, at.name));
```

---

### ✓ `q_game_20251121` (spielergebnis, 14.3s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Selber Wölfe und Heilbronner Falken am 2025-11-21?

**Erwartet:** `['1:6', '1-6', '1 zu 6']`

**Antwort:** Das Spiel zwischen Selber Wölfe und Heilbronner Falken am 2025-11-21 endete mit dem Ergebnis Selber Wölfe 1:6 Heilbronner Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-11-21' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Selber Wölfe' IN (ht.name, at.name));
```

---

### ✓ `q_game_20251116` (spielergebnis, 27.5s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen SC Riessersee und Heilbronner Falken am 2025-11-16?

**Erwartet:** `['1:6', '1-6', '1 zu 6']`

**Antwort:** Das Spiel zwischen SC Riessersee und Heilbronner Falken am 2025-11-16 endete mit SC Riessersee 1:6 Heilbronner Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-11-16' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('SC Riessersee' IN (ht.name, at.name));
```

---

### ✓ `q_game_20251114` (spielergebnis, 10.1s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und Erding Gladiators am 2025-11-14?

**Erwartet:** `['7:2', '7-2', '7 zu 2']`

**Antwort:** Das Spiel zwischen den Heilbronner Falken und den Erding Gladiators am 14.11.2025 endete 7:2 für die Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-11-14' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Erding Gladiators' IN (ht.name, at.name));
```

---

### ✓ `q_game_20251028` (spielergebnis, 11.2s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und Bayreuth Tigers am 2025-10-28?

**Erwartet:** `['10:1', '10-1', '10 zu 1']`

**Antwort:** Das Spiel zwischen den Heilbronner Falken und den Bayreuth Tigers am 2025-10-28 endete 10:1 für die Heilbronner Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-10-28' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Bayreuth Tigers' IN (ht.name, at.name));
```

---

### ✓ `q_game_20251017` (spielergebnis, 24.5s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und EV Füssen am 2025-10-17?

**Erwartet:** `['7:1', '7-1', '7 zu 1']`

**Antwort:** Das Spiel zwischen den Heilbronner Falken und dem EV Füssen am 17. Oktober 2025 endete 7:1 (Heilbronner Falken 7:1 EV Füssen).

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-10-17' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('EV Füssen' IN (ht.name, at.name))
```

---

### ✓ `q_game_20251010` (spielergebnis, 9.9s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Stuttgart Rebels und Heilbronner Falken am 2025-10-10?

**Erwartet:** `['1:9', '1-9', '1 zu 9']`

**Antwort:** Das Spiel zwischen den Stuttgart Rebels und den Heilbronner Falken am 2025-10-10 endete 1:9 für die Gäste.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-10-10' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Stuttgart Rebels' IN (ht.name, at.name));
```

---

### ✓ `q_game_20250216` (spielergebnis, 9.5s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen EV Füssen und Heilbronner Falken am 2025-02-16?

**Erwartet:** `['2:7', '2-7', '2 zu 7']`

**Antwort:** Das Spiel zwischen EV Füssen und Heilbronner Falken am 2025-02-16 endete mit EV Füssen 2:7 Heilbronner Falken.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-02-16' AND ('EV Füssen' IN (ht.name, at.name)) AND ('Heilbronner Falken' IN (ht.name, at.name));
```

---

### ✓ `q_game_20250214` (spielergebnis, 36.4s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und EC Peiting am 2025-02-14?

**Erwartet:** `['8:2', '8-2', '8 zu 2']`

**Antwort:** Das Spiel endete mit einem 8:2-Sieg der Heilbronner Falken gegen den EC Peiting.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-02-14' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('EC Peiting' IN (ht.name, at.name))
```

---

### ✓ `q_game_20250211` (spielergebnis, 16.0s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Heilbronner Falken und Bayreuth Tigers am 2025-02-11?

**Erwartet:** `['9:4', '9-4', '9 zu 4']`

**Antwort:** Das Spiel zwischen den Heilbronner Falken und den Bayreuth Tigers am 2025-02-11 endete mit einem Ergebnis von Heilbronner Falken 9:4 Bayreuth Tigers.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-02-11' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Bayreuth Tigers' IN (ht.name, at.name));
```

---

### ✓ `q_game_20250126` (spielergebnis, 10.9s)

**Frage:** Welches Ergebnis hatte das Spiel zwischen Stuttgart Rebels und Heilbronner Falken am 2025-01-26?

**Erwartet:** `['1:6', '1-6', '1 zu 6']`

**Antwort:** Das Spiel zwischen den Stuttgart Rebels und den Heilbronner Falken am 2025-01-26 endete mit einem Ergebnis von Stuttgart Rebels 1:6 Heilbronner Falken.

```sql
SELECT g.date, ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE g.date::date = '2025-01-26' AND ('Stuttgart Rebels' IN (ht.name, at.name)) AND ('Heilbronner Falken' IN (ht.name, at.name));
```

---

### ✓ `q_po_2022_23_play-down` (playoff, 22.1s)

**Frage:** Wer gewann die Play-Down R1-Serie zwischen Falken und Selber Wölfe in der Saison 2022/23?

**Erwartet:** `['Selber Wölfe']`

**Antwort:** Die Selber Wölfe gewannen die Play-Down R1-Serie gegen die Heilbronner Falken in der Saison 2022/23 mit 4:2.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2022/23' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('Selber Wölfe' IN (ta.name, tb.name)) AND ps.round = 'Play-Down R1';
```

---

### ✓ `q_po_2022_23_play-down` (playoff, 35.8s)

**Frage:** Wer gewann die Play-Down R2-Serie zwischen Falken und Bayreuth Tigers in der Saison 2022/23?

**Erwartet:** `['Bayreuth Tigers']`

**Antwort:** Die Bayreuth Tigers gewannen die Play-Down R2-Serie gegen die Heilbronner Falken in der Saison 2022/23 mit 4:2 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2022/23' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('Bayreuth Tigers' IN (ta.name, tb.name)) AND ps.round = 'Play-Down R2';
```

---

### ✓ `q_po_2021_22_viertelfin` (playoff, 10.6s)

**Frage:** Wer gewann die Viertelfinale-Serie zwischen Falken und Eispiraten Crimmitschau in der Saison 2021/22?

**Erwartet:** `['Heilbronner Falken']`

**Antwort:** Die Heilbronner Falken gewannen die Viertelfinale-Serie gegen die Eispiraten Crimmitschau in der Saison 2021/22 mit 4:0 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2021/22' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('Eispiraten Crimmitschau' IN (ta.name, tb.name)) AND ps.round = 'Viertelfinale';
```

---

### ✓ `q_po_2021_22_halbfinale` (playoff, 31.8s)

**Frage:** Wer gewann die Halbfinale-Serie zwischen Falken und Löwen Frankfurt in der Saison 2021/22?

**Erwartet:** `['Löwen Frankfurt']`

**Antwort:** Löwen Frankfurt gewann die Halbfinale-Serie mit 4:0 gegen die Heilbronner Falken.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2021/22' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('Löwen Frankfurt' IN (ta.name, tb.name)) AND ps.round = 'Halbfinale';
```

---

### ✓ `q_po_2020_21_viertelfin` (playoff, 10.2s)

**Frage:** Wer gewann die Viertelfinale-Serie zwischen Falken und Kassel Huskies in der Saison 2020/21?

**Erwartet:** `['Kassel Huskies']`

**Antwort:** Die Kassel Huskies gewannen die Viertelfinale-Serie gegen die Heilbronner Falken mit 3:0 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2020/21' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('Kassel Huskies' IN (ta.name, tb.name)) AND ps.round = 'Viertelfinale';
```

---

### ✓ `q_po_2018_19_preplay-o` (playoff, 21.6s)

**Frage:** Wer gewann die Pre Play-Off-Serie zwischen Falken und Dresdner Eislöwen in der Saison 2018/19?

**Erwartet:** `['Dresdner Eislöwen']`

**Antwort:** Die Dresdner Eislöwen gewannen die Pre Play-Off-Serie gegen die Heilbronner Falken mit 2:1 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2018/19' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('Dresdner Eislöwen' IN (ta.name, tb.name)) AND ps.round = 'Pre Play-Off';
```

---

### ✓ `q_po_2017_18_preplay-o` (playoff, 56.3s)

**Frage:** Wer gewann die Pre Play-Off-Serie zwischen Falken und Dresdner Eislöwen in der Saison 2017/18?

**Erwartet:** `['Heilbronner Falken']`

**Antwort:** Die Heilbronner Falken gewannen die Pre Play-Off-Serie gegen die Dresdner Eislöwen mit 2:0 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2017/18'   AND ('Heilbronner Falken' IN (ta.name, tb.name))   AND ('Dresdner Eislöwen' IN (ta.name, tb.name))   AND ps.round ILIKE '%Pre%';
```

---

### ✓ `q_po_2017_18_viertelfin` (playoff, 18.6s)

**Frage:** Wer gewann die Viertelfinale-Serie zwischen Falken und SC Bietigheim-Bissingen Steelers in der Saison 2017/18?

**Erwartet:** `['SC Bietigheim-Bissingen Steelers']`

**Antwort:** Der SC Bietigheim-Bissingen Steelers gewann die Viertelfinale-Serie gegen die Heilbronner Falken mit 4:1 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2017/18' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('SC Bietigheim-Bissingen Steelers' IN (ta.name, tb.name)) AND ps.round = 'Viertelfinale';
```

---

### ✓ `q_po_2016_17_play-down` (playoff, 22.5s)

**Frage:** Wer gewann die Play-Down R1-Serie zwischen Falken und StarBulls Rosenheim in der Saison 2016/17?

**Erwartet:** `['Heilbronner Falken']`

**Antwort:** Die Heilbronner Falken gewannen die Play-Down R1-Serie gegen die StarBulls Rosenheim mit 4:2 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2016/17' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('StarBulls Rosenheim' IN (ta.name, tb.name)) AND ps.round = 'Play-Down R1';
```

---

### ✓ `q_po_2015_16_play-down` (playoff, 20.5s)

**Frage:** Wer gewann die Play-Down R2-Serie zwischen Falken und ESV Kaufbeuren in der Saison 2015/16?

**Erwartet:** `['ESV Kaufbeuren']`

**Antwort:** Die Play-Down R2-Serie zwischen den Heilbronner Falken und ESV Kaufbeuren in der Saison 2015/16 gewann ESV Kaufbeuren mit 4:3.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2015/16' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('ESV Kaufbeuren' IN (ta.name, tb.name)) AND ps.round = 'Play-Down R2';
```

---

### ✓ `q_po_2015_16_play-down` (playoff, 17.2s)

**Frage:** Wer gewann die Play-Down R1-Serie zwischen Falken und Lausitzer Füchse in der Saison 2015/16?

**Erwartet:** `['Lausitzer Füchse']`

**Antwort:** Die Lausitzer Füchse gewannen die Play-Down R1-Serie gegen die Heilbronner Falken in der Saison 2015/16 mit 4:1-Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2015/16' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('Lausitzer Füchse' IN (ta.name, tb.name)) AND ps.round = 'Play-Down R1';
```

---

### ✓ `q_po_2014_15_play-down` (playoff, 14.0s)

**Frage:** Wer gewann die Play-Down R2-Serie zwischen Falken und ESV Kaufbeuren in der Saison 2014/15?

**Erwartet:** `['ESV Kaufbeuren']`

**Antwort:** Der ESV Kaufbeuren gewann die Play-Down R2-Serie gegen die Heilbronner Falken in der Saison 2014/15 mit 4:2 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2014/15' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('ESV Kaufbeuren' IN (ta.name, tb.name)) AND ps.round = 'Play-Down R2';
```

---

### ✓ `q_po_2014_15_play-down` (playoff, 15.7s)

**Frage:** Wer gewann die Play-Down R1-Serie zwischen Falken und Eispiraten Crimmitschau in der Saison 2014/15?

**Erwartet:** `['Eispiraten Crimmitschau']`

**Antwort:** Die Eispiraten Crimmitschau gewannen die Play-Down R1-Serie gegen die Falken in der Saison 2014/15 mit 4:1.

```sql
SELECT wt.name AS winner, ps.wins_a, ps.wins_b FROM playoff_series ps JOIN seasons s ON s.id = ps.season_id JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id WHERE s.label = '2014/15' AND ps.round = 'Play-Down R1' AND ((ta.name = 'Heilbronner Falken' AND tb.name = 'Eispiraten Crimmitschau') OR (ta.name = 'Eispiraten Crimmitschau' AND tb.name = 'Heilbronner Falken'));
```

---

### ✓ `q_po_2013_14_play-down` (playoff, 9.8s)

**Frage:** Wer gewann die Play-Down-Serie zwischen Falken und ESV Kaufbeuren in der Saison 2013/14?

**Erwartet:** `['Heilbronner Falken']`

**Antwort:** Die Heilbronner Falken gewannen die Play-Down-Serie gegen den ESV Kaufbeuren in der Saison 2013/14.

```sql
SELECT wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2013/14' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('ESV Kaufbeuren' IN (ta.name, tb.name)) AND (ps.round ILIKE 'play-down%')
```

---

### ✓ `q_po_2012_13_viertelfin` (playoff, 11.6s)

**Frage:** Wer gewann die Viertelfinale-Serie zwischen Falken und Schwenninger Wild Wings in der Saison 2012/13?

**Erwartet:** `['Schwenninger Wild Wings']`

**Antwort:** Die Schwenninger Wild Wings gewannen die Viertelfinale-Serie gegen die Heilbronner Falken mit 4:1 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2012/13' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('Schwenninger Wild Wings' IN (ta.name, tb.name)) AND ps.round = 'Viertelfinale';
```

---

### ✓ `q_po_2011_12_viertelfin` (playoff, 26.0s)

**Frage:** Wer gewann die Viertelfinale-Serie zwischen Falken und Ravensburg Towerstars in der Saison 2011/12?

**Erwartet:** `['Ravensburg Towerstars']`

**Antwort:** Die Viertelfinale-Serie zwischen den Heilbronner Falken und den Ravensburg Towerstars in der Saison 2011/12 gewannen die Ravensburg Towerstars mit 4:3 Siegen.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2011/12' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('Ravensburg Towerstars' IN (ta.name, tb.name)) AND ps.round = 'Viertelfinale'
```

---

### ✓ `q_po_2010_11_viertelfin` (playoff, 10.6s)

**Frage:** Wer gewann die Viertelfinale-Serie zwischen Falken und StarBulls Rosenheim in der Saison 2010/11?

**Erwartet:** `['StarBulls Rosenheim']`

**Antwort:** Die StarBulls Rosenheim gewannen die Viertelfinale-Serie gegen die Heilbronner Falken in der Saison 2010/11 mit 4:0.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2010/11' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ('StarBulls Rosenheim' IN (ta.name, tb.name)) AND ps.round = 'Viertelfinale';
```

---

### ✓ `q_trend_001` (trend, 22.9s)

**Frage:** Welches war die punkteschlechteste Falken-Saison der letzten 10 Jahre?

**Erwartet:** `['2015/16', '36']`

**Antwort:** Die punkteschlechteste Saison der letzten 10 Jahre war die Saison 2015/16 mit 36 Punkten.

```sql
SELECT season, points FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND season >= '2015/16' ORDER BY points ASC NULLS LAST LIMIT 1;
```

---

### ✗ `q_trend_002` (trend, 22.7s)

**Frage:** In welcher Saison hatten die Falken die meisten Punkte?

**Erwartet:** `['2006/07', '108']`

**Antwort:** Die Falken hatten in der Saison 2024/25 mit 114 Punkten die meisten Punkte.

```sql
SELECT season, points FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE ORDER BY points DESC NULLS LAST LIMIT 1;
```

**Fehlende Fakten:** `['2006/07', '108']`

---

### ✓ `q_trend_003` (trend, 17.0s)

**Frage:** Wie viele DEL2-Saisons haben die Falken insgesamt gespielt?

**Erwartet:** `['10']`

**Antwort:** Die Heilbronner Falken haben insgesamt 10 DEL2-Saisons gespielt.

```sql
SELECT COUNT(DISTINCT season) AS del2_seasons FROM season_standings WHERE team = 'Heilbronner Falken' AND league = 'DEL2' AND is_focus_team_season = TRUE;
```

---

### ✗ `q_trend_004` (trend, 37.2s)

**Frage:** Wann war der letzte Falken-Abstieg aus der DEL2?

**Erwartet:** `['2022/23']`

**Antwort:** Es liegen keine Daten vor.

```sql
SELECT season FROM season_standings WHERE team = 'Heilbronner Falken' AND league = 'DEL2' AND playoff_result = 'Abstieg' ORDER BY season DESC LIMIT 1
```

**Fehlende Fakten:** `['2022/23']`

---

### ✗ `q_trend_005` (trend, 15.2s)

**Frage:** Welcher Spieler hat die meisten Falken-Saisons als Topscorer?

**Erwartet:** `['Dylan Wruck']`

**Antwort:** _(leer)_

```sql
SELECT player, COUNT(*) AS seasons_as_topscorer FROM (SELECT season, player, points, ROW_NUMBER() OVER (PARTITION BY season ORDER BY points DESC NULLS LAST) AS rn FROM falken_skater_stats WHERE points IS NOT NULL) sub WHERE rn = 1 GROUP BY player ORDER BY seasons_as_topscorer DESC NULLS LAST LIMIT 1;
```

**Fehlende Fakten:** `['Dylan Wruck']`

---

### ✗ `q_trend_006` (trend, 21.1s)

**Frage:** Wie viele Saisons spielten die Falken in der Oberliga in den letzten Jahren?

**Erwartet:** `['3']`

**Antwort:** Die Heilbronner Falken spielten in den letzten Jahren 10 Saisons in der Oberliga.

```sql
SELECT COUNT(DISTINCT season) AS anzahl_saisons FROM season_standings WHERE team = 'Heilbronner Falken' AND league IN ('Oberliga', 'Oberliga Süd') AND is_focus_team_season = TRUE;
```

**Fehlende Fakten:** `['3']`

---

### ✗ `q_trend_007` (trend, 28.2s)

**Frage:** In welcher Saison war die Hauptrunde am kürzesten (wegen Corona)?

**Erwartet:** `['2020/21', '49']`

**Antwort:** _(leer)_

```sql
SELECT s.label AS season, MIN(s.end_date - s.start_date) AS days FROM seasons s JOIN team_seasons ts ON ts.season_id = s.id JOIN teams t ON t.id = ts.team_id WHERE t.name = 'Heilbronner Falken' AND s.league IN ('DEL2', 'Oberliga Süd', 'Oberliga') GROUP BY s.label ORDER BY days ASC NULLS LAST LIMIT 1;
```

**Fehlende Fakten:** `['2020/21', '49']`

---

### ✗ `q_trend_008` (trend, 17.4s)

**Frage:** Welcher Trainer hatte die längste Amtszeit bei den Falken?

**Erwartet:** `['Rico Rossi']`

**Antwort:** Georges Hüttig hatte mit 273 Tagen (vom 1. September 1983 bis zum 31. Mai 1984) die längste Amtszeit bei den Falken.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date, (ct.end_date - ct.start_date) AS tenure_days FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id WHERE t.name = 'Heilbronner Falken' AND ct.role = 'Headcoach' AND ct.end_date IS NOT NULL AND ct.start_date IS NOT NULL ORDER BY tenure_days DESC NULLS LAST LIMIT 1;
```

**Fehlende Fakten:** `['Rico Rossi']`

---

### ✗ `q_trend_009` (trend, 70.8s)

**Frage:** Wie viele Trainer hatten die Falken in der DEL2-Zeit (2013-2023)?

**Erwartet:** `[]`

**Antwort:** In der DEL2-Zeit von 2013 bis 2023 hatten die Falken 12 Trainer.

```sql
SELECT COUNT(DISTINCT c.name) AS num_coaches FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label >= '2013/14' AND s.label <= '2022/23' AND ct.role = 'Headcoach';
```

---

### ✓ `q_trend_010` (trend, 145.0s)

**Frage:** Was war das höchste Falken-Tor-Ergebnis in der aktuellen Saison?

**Erwartet:** `['11']`

**Antwort:** Das höchste Falken-Tor-Ergebnis in der aktuellen Saison war 11:3 im Spiel Heilbronner Falken gegen Bayreuth Tigers.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id JOIN seasons s ON s.id = g.season_id WHERE ('Heilbronner Falken' IN (ht.name, at.name)) AND s.label = (SELECT label FROM seasons WHERE league = 'DEL2' ORDER BY start_date DESC LIMIT 1) ORDER BY GREATEST(g.home_score, g.away_score) DESC NULLS LAST LIMIT 1
```

---

### ✓ `q_trend_011` (trend, 25.1s)

**Frage:** In welcher Saison wurden die Falken Oberliga-Meister?

**Erwartet:** `['2006/07']`

**Antwort:** Die Falken wurden in der Saison 2006/07 Oberliga-Meister.

```sql
SELECT season FROM season_standings WHERE team = 'Heilbronner Falken' AND playoff_result = 'Meister' AND league LIKE 'Oberliga%' AND is_focus_team_season = TRUE ORDER BY season DESC LIMIT 1;
```

---

### ✗ `q_trend_012` (trend, 16.2s)

**Frage:** Wann hatten die Falken zuletzt mehr als 100 Punkte?

**Erwartet:** `['2006/07', '108']`

**Antwort:** Die Falken hatten zuletzt in der Saison 2024/25 mit 114 Punkten mehr als 100 Punkte.

```sql
SELECT season, points FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND points > 100 ORDER BY season DESC NULLS LAST LIMIT 1;
```

**Fehlende Fakten:** `['2006/07', '108']`

---

### ✗ `q_trend_013` (trend, 31.3s)

**Frage:** Wer war Topscorer in der letzten Oberliga-Süd-Saison?

**Erwartet:** `['Wernerson Libäck', 'Ritchie']`

**Antwort:** Calder ANDERSON war mit 68 Punkten (30 Tore, 38 Assists) der Topscorer der letzten Oberliga-Süd-Saison.

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = (SELECT season FROM season_standings WHERE team = 'Heilbronner Falken' AND league = 'Oberliga Süd' AND is_focus_team_season = TRUE ORDER BY season DESC LIMIT 1) AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 5;
```

**Fehlende Fakten:** `['Wernerson Libäck', 'Ritchie']`

---

### ✗ `q_trend_014` (trend, 12.5s)

**Frage:** Wie viele unterschiedliche Trainer hatten die Falken seit 1980?

**Erwartet:** `[]`

**Antwort:** Die Heilbronner Falken hatten seit 1980 insgesamt 34 unterschiedliche Trainer.

```sql
SELECT COUNT(DISTINCT c.id) AS trainer_count FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.start_date >= '1980-01-01' AND ct.role = 'Headcoach';
```

---

### ✓ `q_trend_015` (trend, 23.0s)

**Frage:** Welche Liga ist die zweite deutsche Eishockey-Liga heute?

**Erwartet:** `['DEL2']`

**Antwort:** Die zweite deutsche Eishockey-Liga ist heute die DEL2.

```sql
SELECT 'DEL2' AS second_division_league;
```

---

### ✗ `q_compare_001` (vergleich, 13.8s)

**Frage:** Wie oft haben die Falken in der Saison 2025/26 gegen Bayreuth gespielt?

**Erwartet:** `['4']`

**Antwort:** Die Falken haben in der Saison 2025/26 kein Spiel gegen Bayreuth bestritten (0 Spiele).

```sql
SELECT COUNT(*) AS total_games FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id JOIN seasons s ON s.id = g.season_id WHERE s.label = '2025/26' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('Bayreuth' IN (ht.name, at.name));
```

**Fehlende Fakten:** `['4']`

---

### ✓ `q_compare_002` (vergleich, 25.9s)

**Frage:** Welches war das höchste Falken-Heim-Ergebnis gegen Bayreuth?

**Erwartet:** `['11']`

**Antwort:** Das höchste Falken-Heim-Ergebnis gegen Bayreuth war ein 11:3-Sieg am 6. Februar 2026 (Saison 2025/26).

```sql
SELECT g.home_score, g.away_score, g.date, s.label AS season FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id JOIN seasons s ON s.id = g.season_id WHERE ht.name = 'Heilbronner Falken'   AND at.name ILIKE '%Bayreuth%'   AND g.home_score IS NOT NULL ORDER BY g.home_score DESC NULLS LAST LIMIT 1;
```

---

### ✗ `q_compare_003` (vergleich, 20.2s)

**Frage:** Wann haben die Falken zuletzt im Halbfinale gespielt?

**Erwartet:** `['2021/22', '2023/24']`

**Antwort:** Die Heilbronner Falken haben zuletzt in der Saison 2024/25 im Halbfinale gespielt.

```sql
SELECT s.label AS season FROM playoff_series ps JOIN seasons s ON s.id = ps.season_id JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id WHERE ('Heilbronner Falken' IN (ta.name, tb.name))   AND ps.round = 'Halbfinale' ORDER BY s.start_date DESC NULLS LAST LIMIT 1;
```

**Fehlende Fakten:** `['2021/22', '2023/24']`

---

### ✗ `q_compare_004` (vergleich, 55.2s)

**Frage:** Gegen welches Team verloren die Falken 2022/23 in den Playdowns?

**Erwartet:** `['Bayreuth']`

**Antwort:** _(leer)_

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2022/23' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ps.round LIKE 'Play-Down%' AND wt.name != 'Heilbronner Falken'
```

**Fehlende Fakten:** `['Bayreuth']`

---

### ✓ `q_compare_005` (vergleich, 10.5s)

**Frage:** Wer wurde Hauptrundensieger der Oberliga Süd 2024/25?

**Erwartet:** `['Heilbronner Falken', 'Falken']`

**Antwort:** Der Hauptrundensieger der Oberliga Süd 2024/25 sind die Heilbronner Falken mit 114 Punkten.

```sql
SELECT team, final_rank, points FROM season_standings WHERE league = 'Oberliga Süd' AND season = '2024/25' ORDER BY final_rank ASC LIMIT 1;
```

---

### ✗ `q_compare_006` (vergleich, 21.5s)

**Frage:** Wie viele Spiele hat die DEL2 in einer normalen Saison?

**Erwartet:** `['52']`

**Antwort:** In einer normalen Saison hat die DEL2 364 Spiele.

```sql
SELECT COUNT(DISTINCT g.id) AS total_games FROM games g JOIN seasons s ON s.id = g.season_id WHERE s.league = 'DEL2' AND g.game_type = 'regular' AND s.label = (SELECT label FROM seasons WHERE league = 'DEL2' ORDER BY start_date DESC NULLS LAST LIMIT 1);
```

**Fehlende Fakten:** `['52']`

---

### ✓ `q_compare_007` (vergleich, 11.4s)

**Frage:** Hat Stefan Della Rovere mehr als 30 Punkte in 2022/23?

**Erwartet:** `['38']`

**Antwort:** Ja, Stefan Della Rovere erzielte in der Saison 2022/23 38 Punkte und damit mehr als 30.

```sql
SELECT player, points FROM falken_skater_stats WHERE similarity(player, 'Stefan Della Rovere') > 0.3 AND season = '2022/23' AND points IS NOT NULL ORDER BY similarity(player, 'Stefan Della Rovere') DESC LIMIT 1;
```

---

### ✓ `q_compare_008` (vergleich, 12.2s)

**Frage:** Wie viele Punkte hatten die Falken in 2019/20?

**Erwartet:** `['84']`

**Antwort:** Die Falken hatten in der Saison 2019/20 84 Punkte.

```sql
SELECT points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2019/20' AND is_focus_team_season = TRUE;
```

---

### ✓ `q_compare_009` (vergleich, 9.7s)

**Frage:** Welche Saisons hatte Dylan Wruck mehr als 75 Punkte?

**Erwartet:** `['2019/20', '2020/21']`

**Antwort:** Dylan Wruck hatte in den Saisons 2019/20 (88 Punkte) und 2020/21 (78 Punkte) mehr als 75 Punkte.

```sql
SELECT season, points, goals, assists FROM falken_skater_stats WHERE similarity(player, 'Dylan Wruck') > 0.3 AND points > 75 ORDER BY season DESC;
```

---

### ✓ `q_compare_010` (vergleich, 11.2s)

**Frage:** Wer war Falken-Topscorer in der Klassenerhaltsaison 2015/16?

**Erwartet:** `['Adam Brace']`

**Antwort:** Adam Brace war der Topscorer der Heilbronner Falken in der Klassenerhaltsaison 2015/16 mit 63 Punkten (28 Tore, 35 Assists).

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = '2015/16' AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

---
