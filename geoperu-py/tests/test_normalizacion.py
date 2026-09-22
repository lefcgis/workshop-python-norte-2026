from geoperu.normalizacion import DEPARTAMENTOS, es_departamento, normalizar, sugerir


class TestNormalizar:
    def test_mayusculas_y_espacios(self):
        assert normalizar("  Madre de Dios ") == "MADRE DE DIOS"

    def test_las_tres_formas_resuelven_igual(self):
        # El error más común de esta biblioteca es un nombre mal capitalizado.
        formas = ["MADRE DE DIOS", "Madre de Dios", "madre de dios", "  madre  de  dios  "]
        assert len({normalizar(f) for f in formas}) == 1

    def test_quita_tildes(self):
        assert normalizar("Áncash") == "ANCASH"
        assert normalizar("Apurímac") == "APURIMAC"
        assert normalizar("Junín") == "JUNIN"

    def test_la_dieresis_va_a_u(self):
        # Divergencia documentada: peruocc la manda a "D" por un desliz en su
        # tabla de reemplazo. Ninguna unidad del Perú lleva diéresis.
        assert normalizar("GÜEMES") == "GUEMES"

    def test_enie(self):
        assert normalizar("Ñuñoa") == "NUNOA"

    def test_quita_puntuacion(self):
        assert normalizar("San Martín-Tarapoto.") == "SAN MARTINTARAPOTO"

    def test_nulo(self):
        assert normalizar(None) is None


class TestDepartamentos:
    def test_son_veinticinco(self):
        assert len(DEPARTAMENTOS) == 25

    def test_coinciden_con_peruocc(self):
        assert DEPARTAMENTOS[0] == "AMAZONAS"
        assert DEPARTAMENTOS[-1] == "UCAYALI"
        assert "CALLAO" in DEPARTAMENTOS
        assert "LA LIBERTAD" in DEPARTAMENTOS

    def test_ya_estan_normalizados(self):
        assert all(normalizar(d) == d for d in DEPARTAMENTOS)

    def test_reconocimiento(self):
        assert es_departamento("madre de dios")
        assert not es_departamento("Tarapoto")


class TestSugerir:
    def test_propone_el_parecido(self):
        assert "MADRE DE DIOS" in sugerir("madre de dias", DEPARTAMENTOS)

    def test_sin_parecido_no_inventa(self):
        assert sugerir("zzzzzzzz", DEPARTAMENTOS) == ()
