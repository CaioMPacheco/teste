import copy
import json
import os
import re
import shutil
import struct
import subprocess
import zlib

from datetime import datetime
from pathlib import Path


BASE = Path(__file__).resolve().parent

PROJECT = (
    BASE if (BASE / "build.gradle").exists()
    else BASE / "DragonMineZ-Legends"
)

SRC = (
    PROJECT / "src/main/java/dev/caiopacheco/dmzlegends"
)

RES = PROJECT / "src/main/resources"

INSTANCIA = (
    Path(os.environ["APPDATA"])
    / ".sklauncher/instances/dragon-mine-z-att"
)

BACKUP = (
    BASE / "backups_v03"
    / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
)

BOSSES = {
    "beerus": {
        "hp": 18000000,
        "skin": "#9868B9",
        "outfit": "#193C78",
        "accent": "#F1C44B",
        "eyes": "#EACC37"
    },
    "jiren": {
        "hp": 25000000,
        "skin": "#AEB0B4",
        "outfit": "#B51E2E",
        "accent": "#24242C",
        "eyes": "#101015"
    },
    "demigra": {
        "hp": 32000000,
        "skin": "#A98BC6",
        "outfit": "#552044",
        "accent": "#D7AD56",
        "eyes": "#E93057"
    },
    "golden_frieza": {
        "hp": 11000000,
        "skin": "#EDC34A",
        "outfit": "#D9AE35",
        "accent": "#8A43AD",
        "eyes": "#C73643"
    },
    "hit": {
        "hp": 14000000,
        "skin": "#9A77B4",
        "outfit": "#34304E",
        "accent": "#897AAB",
        "eyes": "#C43154"
    },
    "goku_black": {
        "hp": 16000000,
        "skin": "#D6AA97",
        "outfit": "#33333A",
        "accent": "#BF486A",
        "eyes": "#363035"
    }
}


def salvar(path, conteudo):
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        copia = BACKUP / "arquivos" / path.name

        copia.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(path, copia)

    path.write_text(conteudo, encoding="utf-8")


def salvar_json(path, dados):
    salvar(
        path,
        json.dumps(dados, indent=2, ensure_ascii=False)
    )


def atualizar_java():
    arquivo = SRC / "Legends.java"

    texto = arquivo.read_text(encoding="utf-8-sig")

    if 'register("golden_frieza")' not in texto:
        marcador = 'register("demigra");'

        if marcador not in texto:
            raise RuntimeError(
                "Registro de Demigra não encontrado."
            )

        texto = texto.replace(
            marcador,
            marcador + """

        register("golden_frieza");
        register("hit");
        register("goku_black");"""
        )

    texto, quantidade = re.subn(
        r"double health = switch \(entry.getKey\(\)\) \{.*?\};",
        "double health = 1024.0D;",
        texto,
        count=1,
        flags=re.S
    )

    if quantidade != 1 and "double health = 1024.0D;" not in texto:
        raise RuntimeError(
            "Não foi possível localizar o registro de vida."
        )

    salvar(arquivo, texto)

    print("[OK] Registro dos seis chefes atualizado.")


def atualizar_combate():
    arquivo = SRC / "LegendBoss.java"

    texto = arquivo.read_text(encoding="utf-8-sig")

    if "legendsHealthReady" not in texto:

        texto = texto.replace(
            "private int casting = 0;",
            """private int casting = 0;
    private boolean legendsHealthReady = false;"""
        )

    if "public float getMaxHealth()" not in texto:

        marcador = (
            "    @Override\n"
            "    protected void defineSynchedData()"
        )

        adicional = """
    @Override
    public float getMaxHealth() {
        return switch (kind()) {
            case "beerus" -> 18000000.0F;
            case "jiren" -> 25000000.0F;
            case "demigra" -> 32000000.0F;
            case "golden_frieza" -> 11000000.0F;
            case "hit" -> 14000000.0F;
            case "goku_black" -> 16000000.0F;
            default -> 1000000.0F;
        };
    }

    @Override
    protected void addAdditionalSaveData(
        net.minecraft.nbt.CompoundTag tag
    ) {
        super.addAdditionalSaveData(tag);

        tag.putBoolean(
            "LegendsHealthReady",
            legendsHealthReady
        );
    }

    @Override
    protected void readAdditionalSaveData(
        net.minecraft.nbt.CompoundTag tag
    ) {
        super.readAdditionalSaveData(tag);

        legendsHealthReady = tag.getBoolean(
            "LegendsHealthReady"
        );
    }

"""

        if marcador not in texto:
            raise RuntimeError(
                "Não foi possível inserir o sistema de vida."
            )

        texto = texto.replace(
            marcador,
            adicional + marcador
        )

    if "if (!legendsHealthReady" not in texto:

        marcador = """public void tick() {
        super.tick();"""

        substituicao = """public void tick() {

        if (!level().isClientSide && !legendsHealthReady) {
            setHealth(getMaxHealth());
            legendsHealthReady = true;
        }

        super.tick();"""

        if marcador not in texto:
            raise RuntimeError(
                "Método tick não encontrado."
            )

        texto = texto.replace(
            marcador,
            substituicao
        )

    texto = texto.replace(
        "getMaxHealth() * 0.09F",
        "getMaxHealth() * 0.06F"
    )

    padrao = (
        r"    private float specialDamage"
        r"\(LivingEntity target\) \{.*?"
        r"\n    \}\n\n"
        r"    private void special\("
    )

    substituicao = """    private float specialDamage(LivingEntity target) {

        return Mth.clamp(
            target.getMaxHealth() *
                (0.07F + phase() * 0.035F),
            6.0F,
            1800000.0F
        );
    }

    private void special("""

    texto, quantidade = re.subn(
        padrao,
        lambda _: substituicao,
        texto,
        count=1,
        flags=re.S
    )

    if quantidade != 1:
        raise RuntimeError(
            "Método de dano especial não encontrado."
        )

    if 'case "golden_frieza"' not in texto.split(
        "private void special("
    )[-1]:

        marcador = "            default -> beam(target);"

        novos_ataques = """
            case "golden_frieza" -> {
                beam(target);

                if (phase() >= 3) {
                    beam(target);
                }
            }

            case "hit" -> {
                teleportBehind(target);
                areaAttack(4.0D);
            }

            case "goku_black" -> {
                beam(target);

                if (phase() >= 3) {
                    areaAttack(6.0D);
                }
            }

"""

        if marcador not in texto:
            raise RuntimeError(
                "Local dos ataques especiais não encontrado."
            )

        texto = texto.replace(
            marcador,
            novos_ataques + marcador,
            1
        )

    salvar(arquivo, texto)

    print("[OK] Sistema de combate atualizado.")
    print("[OK] Vida dos chefes ampliada.")
    print("[OK] Novos ataques adicionados.")


def rgb(cor):
    return tuple(
        bytes.fromhex(cor.replace("#", ""))
    ) + (255,)


def gerar_textura(nome, perfil):
    largura = 64
    altura = 64

    pixels = [
        [(0, 0, 0, 0) for _ in range(largura)]
        for _ in range(altura)
    ]

    pele = rgb(perfil["skin"])
    roupa = rgb(perfil["outfit"])
    detalhe = rgb(perfil["accent"])
    olhos = rgb(perfil["eyes"])

    def pintar(x, y, w, h, cor):
        for py in range(max(0, y), min(64, y + h)):
            for px in range(max(0, x), min(64, x + w)):
                pixels[py][px] = cor

    def cubo(u, v, w, h, d, frente, lados=None):
        lados = lados or frente

        pintar(u + d, v, w, d, lados)
        pintar(u + d + w, v, w, d, lados)

        pintar(u, v + d, d, h, lados)
        pintar(u + d, v + d, w, h, frente)

        pintar(u + d + w, v + d, d, h, lados)

        pintar(u + 2 * d + w, v + d, w, h, lados)

    # Cabeça: todas as faces do modelo.
    cubo(0, 0, 8, 8, 8, pele)

    # Tronco.
    cubo(16, 16, 8, 12, 4, roupa)

    # Braços.
    cubo(40, 16, 4, 12, 4, roupa)
    cubo(32, 48, 4, 12, 4, roupa)

    # Pernas.
    cubo(0, 16, 4, 12, 4, roupa)
    cubo(16, 48, 4, 12, 4, roupa)

    # Rosto.
    pintar(10, 11, 2, 1, olhos)
    pintar(14, 11, 2, 1, olhos)

    # Detalhes específicos dos personagens.
    if nome == "beerus":
        pintar(20, 20, 8, 2, detalhe)
        pintar(23, 22, 2, 9, detalhe)
        pintar(20, 29, 8, 2, detalhe)

        pintar(44, 28, 4, 2, detalhe)
        pintar(36, 60, 4, 2, detalhe)

        pintar(4, 29, 4, 3, detalhe)
        pintar(20, 61, 4, 3, detalhe)

    elif nome == "jiren":
        pintar(20, 20, 8, 3, detalhe)
        pintar(23, 23, 2, 6, detalhe)

        pintar(44, 27, 4, 5, detalhe)
        pintar(36, 59, 4, 5, detalhe)

        pintar(4, 28, 4, 4, detalhe)
        pintar(20, 60, 4, 4, detalhe)

    elif nome == "demigra":
        pintar(8, 8, 8, 2, rgb("#7A254F"))

        pintar(20, 20, 8, 2, detalhe)
        pintar(23, 22, 2, 10, detalhe)

        pintar(44, 25, 4, 2, detalhe)
        pintar(36, 57, 4, 2, detalhe)

        pintar(4, 28, 4, 4, detalhe)
        pintar(20, 60, 4, 4, detalhe)

    elif nome == "golden_frieza":
        pintar(10, 8, 4, 4, detalhe)
        pintar(20, 20, 8, 5, detalhe)

        pintar(44, 28, 4, 4, detalhe)
        pintar(36, 60, 4, 4, detalhe)

        pintar(4, 28, 4, 4, detalhe)
        pintar(20, 60, 4, 4, detalhe)

    elif nome == "hit":
        pintar(8, 8, 8, 2, detalhe)
        pintar(20, 20, 8, 3, detalhe)

        pintar(23, 23, 2, 9, detalhe)

        pintar(44, 20, 4, 3, detalhe)
        pintar(36, 52, 4, 3, detalhe)

    elif nome == "goku_black":
        cabelo = rgb("#24212D")

        pintar(8, 8, 8, 3, cabelo)

        pintar(20, 20, 8, 2, detalhe)
        pintar(23, 22, 2, 10, detalhe)

        pintar(44, 28, 4, 4, detalhe)
        pintar(36, 60, 4, 4, detalhe)

    dados = bytearray()

    for linha in pixels:
        dados.append(0)

        for pixel in linha:
            dados.extend(pixel)

    def chunk(tipo, conteudo):
        bruto = tipo + conteudo

        return (
            struct.pack(">I", len(conteudo))
            + bruto
            + struct.pack(
                ">I",
                zlib.crc32(bruto) & 0xFFFFFFFF
            )
        )

    header = struct.pack(
        ">IIBBBBB",
        largura,
        altura,
        8,
        6,
        0,
        0,
        0
    )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(dados)))
        + chunk(b"IEND", b"")
    )

    caminho = (
        RES / "assets/dmzlegends/textures/entity"
        / f"{nome}.png"
    )

    caminho.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if caminho.exists():
        destino = BACKUP / "texturas" / caminho.name
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(caminho, destino)

    caminho.write_bytes(png)


def atualizar_visuais():
    arquivo = SRC / "ClientVisuals.java"

    texto = arquivo.read_text(encoding="utf-8-sig")

    if 'id.equals("golden_frieza")' not in texto:

        marcador = (
            "        return LayerDefinition.create("
            "mesh, 64, 64);"
        )

        geometria = """
        if (id.equals("golden_frieza")) {
            head.addOrReplaceChild(
                "frieza_crest",
                CubeListBuilder.create()
                    .texOffs(0, 0)
                    .addBox(
                        -3.0F, -11.0F, -1.0F,
                        6.0F, 4.0F, 3.0F
                    ),
                PartPose.ZERO
            );
        }

        if (id.equals("hit")) {
            head.addOrReplaceChild(
                "hit_head",
                CubeListBuilder.create()
                    .texOffs(0, 0)
                    .addBox(
                        -3.0F, -10.0F, -2.5F,
                        6.0F, 3.0F, 5.0F
                    ),
                PartPose.ZERO
            );
        }

        if (id.equals("goku_black")) {
            head.addOrReplaceChild(
                "black_hair",
                CubeListBuilder.create()
                    .texOffs(0, 0)
                    .addBox(
                        -4.5F, -12.0F, -4.5F,
                        9.0F, 5.0F, 9.0F
                    ),
                PartPose.ZERO
            );
        }

"""

        if marcador not in texto:
            raise RuntimeError(
                "Estrutura do modelo não encontrada."
            )

        texto = texto.replace(
            marcador,
            geometria + marcador
        )

    salvar(arquivo, texto)

    for nome, perfil in BOSSES.items():
        gerar_textura(nome, perfil)

    arquivo_pt = (
        RES / "assets/dmzlegends/lang/pt_br.json"
    )

    arquivo_en = (
        RES / "assets/dmzlegends/lang/en_us.json"
    )

    nomes = {
        "beerus": "Beerus, Deus da Destruição",
        "jiren": "Jiren, o Cinzento",
        "demigra": "Demigra, Deus Demônio",
        "golden_frieza": "Golden Freeza",
        "hit": "Hit, o Assassino",
        "goku_black": "Goku Black"
    }

    for arquivo, idioma in [
        (arquivo_pt, "pt"),
        (arquivo_en, "en")
    ]:
        dados = {}

        if arquivo.exists():
            dados = json.loads(
                arquivo.read_text(encoding="utf-8-sig")
            )

        for nome in BOSSES:
            chave = f"entity.dmzlegends.{nome}"

            dados[chave] = (
                nomes[nome]
                if idioma == "pt"
                else nome.replace("_", " ").title()
            )

        salvar_json(arquivo, dados)

    print("[OK] Seis texturas PNG geradas.")
    print("[OK] Geometria dos personagens atualizada.")


def atualizar_kaioken():
    candidatos = [
        INSTANCIA / "config/dragonminez",
        INSTANCIA / ".minecraft/config/dragonminez"
    ]

    encontrados = 0

    for pasta in candidatos:
        formas = pasta / "forms/kaioken.json"
        habilidades = pasta / "skills.json"

        if not formas.exists() or not habilidades.exists():
            continue

        encontrados += 1

        dados = json.loads(
            formas.read_text(encoding="utf-8-sig")
        )

        skills = json.loads(
            habilidades.read_text(encoding="utf-8-sig")
        )

        configuracoes = dados["forms"]

        base = copy.deepcopy(configuracoes["x20"])

        # Remove os níveis antigos acima de x20.
        for nome in list(configuracoes):
            resultado = re.fullmatch(r"x(\d+)", nome)

            if resultado and int(resultado.group(1)) > 20:
                del configuracoes[nome]

        for indice in range(1, 11):
            nivel = indice * 100
            nome = f"x{nivel}"

            forma = copy.deepcopy(base)

            poder = round(
                1.65 + 0.38 * indice,
                3
            )

            desgaste = round(
                0.248 + 0.18 * (indice ** 1.5),
                3
            )

            forma["name"] = nome

            forma["unlockOnSkillLevel"] = 5 + indice

            for atributo in [
                "strMultiplier",
                "skpMultiplier",
                "pwrMultiplier"
            ]:
                forma[atributo] = poder

            forma["defMultiplier"] = round(
                poder * 1.08, 3
            )

            forma["speedMultiplier"] = min(
                3.0,
                round(1.65 + 0.1 * indice, 3)
            )

            forma["attackSpeed"] = min(
                3.0,
                round(1.65 + 0.1 * indice, 3)
            )

            forma["healthDrain"] = desgaste

            forma["formStackable"] = True
            forma["stackDrainMultiplier"] = 1.25

            forma["allowFreeTransformOnMastery"] = 0.0

            forma["shareMasteryWith"] = (
                [f"kaioken.x{nivel + 100}"]
                if nivel < 1000 else []
            )

            forma["shareMasteryMultiplier"] = 0.25

            configuracoes[nome] = forma

        configuracoes["x20"]["shareMasteryWith"] = [
            "kaioken.x100"
        ]

        custos_anteriores = (
            skills["skills"]["kaioken"]["costs"]
        )

        skills["skills"]["kaioken"]["costs"] = (
            custos_anteriores[:5]
            + [
                15000 * indice * indice
                for indice in range(1, 11)
            ]
        )

        salvar_json(formas, dados)
        salvar_json(habilidades, skills)

        print("[OK] Kaioken atualizado:", formas)

        print(
            "[INFO] Estágios:",
            ", ".join(configuracoes.keys())
        )

    if encontrados == 0:
        print(
            "[AVISO] Configuração do Kaioken não encontrada."
        )

        print(
            "[AVISO] Confirme a pasta de jogo do SKLauncher."
        )


def atualizar_versao():
    gradle = PROJECT / "build.gradle"

    texto = gradle.read_text(encoding="utf-8-sig")

    texto = texto.replace(
        "version = '0.2.0'",
        "version = '0.3.0'"
    )

    salvar(gradle, texto)

    mods = RES / "META-INF/mods.toml"

    texto = mods.read_text(encoding="utf-8-sig")

    texto = texto.replace(
        'version="0.2.0"',
        'version="0.3.0"'
    )

    salvar(mods, texto)


def compilar():
    print("\n[INFO] Iniciando compilação...")

    log = PROJECT / "compilacao_v03.log"

    with log.open("w", encoding="utf-8") as saida:
        resultado = subprocess.run(
            [
                "cmd",
                "/c",
                "gradlew.bat",
                "clean",
                "build",
                "--no-daemon"
            ],
            cwd=PROJECT,
            stdout=saida,
            stderr=subprocess.STDOUT,
            check=False
        )

    if resultado.returncode != 0:
        print("[ERRO] Compilação não concluída.")

        linhas = log.read_text(
            encoding="utf-8",
            errors="replace"
        ).splitlines()

        for linha in linhas[-50:]:
            print(linha)

        print("\nLog completo:", log)
        return

    pasta = PROJECT / "build/libs"

    jars = list(pasta.glob("dmzlegends-0.3.0.jar"))

    if jars:
        print("\n[OK] Compilação concluída!")
        print("[OK] Novo addon:", jars[0])
    else:
        print(
            "[AVISO] Build concluído, mas JAR não localizado."
        )


def main():
    print("=" * 50)
    print("DRAGONMINE Z: LEGENDS — ATUALIZAÇÃO V0.3")
    print("=" * 50)

    if not (PROJECT / "build.gradle").exists():
        raise SystemExit(
            "Projeto Forge não encontrado."
        )

    print("[INFO] Projeto:", PROJECT)
    print("[INFO] Backup:", BACKUP)

    atualizar_java()
    atualizar_combate()
    atualizar_visuais()
    atualizar_kaioken()
    atualizar_versao()

    compilar()

    print("\nProcesso finalizado.")


if __name__ == "__main__":
    main()