import io
import json
import shutil
import struct
import subprocess
import sys
import urllib.request
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "DragonMineZ-Legends"
JAVA = ROOT / "src/main/java/dev/caiopacheco/dmzlegends"
RES = ROOT / "src/main/resources"

MDK = (
    "https://maven.minecraftforge.net/net/minecraftforge/forge/"
    "1.20.1-47.4.10/forge-1.20.1-47.4.10-mdk.zip"
)

BOSSES = {
    "beerus": {
        "name": "Beerus",
        "skin": "#9560B6",
        "outfit": "#173B78",
        "accent": "#F6CB54",
        "eyes": "#E8C938"
    },
    "jiren": {
        "name": "Jiren",
        "skin": "#AAAAAA",
        "outfit": "#B51E27",
        "accent": "#202024",
        "eyes": "#111111"
    },
    "demigra": {
        "name": "Demigra",
        "skin": "#B59AD5",
        "outfit": "#592044",
        "accent": "#D9A649",
        "eyes": "#E63153"
    }
}


def write(relative, content):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def install_mdk():
    projeto = ROOT
    gradle = projeto / "gradlew.bat"

    if gradle.is_file():
        print("[OK] Forge MDK já instalado.")
        return

    arquivo_zip = (
        Path(__file__).resolve().parent
        / "forge-1.20.1-47.4.10-mdk.zip"
    )

    if not arquivo_zip.is_file():
        raise FileNotFoundError(
            f"Arquivo Forge MDK não encontrado: {arquivo_zip}"
        )

    print("[INFO] Instalando Forge MDK pelo arquivo local...")

    projeto.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(arquivo_zip, "r") as zip_ref:
        if "gradlew.bat" not in zip_ref.namelist():
            raise ValueError(
                "O ZIP selecionado não parece ser o Forge MDK."
            )

        zip_ref.extractall(projeto)

    if not gradle.is_file():
        raise RuntimeError(
            "O Gradle não foi encontrado após a extração."
        )

    print("[OK] Forge MDK extraído com sucesso!")


def create_gradle():
    write("gradle.properties", """
org.gradle.jvmargs=-Xmx3G
org.gradle.daemon=false
minecraft_version=1.20.1
minecraft_version_range=[1.20.1,1.20.2)
forge_version=47.4.10
forge_version_range=[47.4.10,)
loader_version_range=[47,)
mapping_channel=official
mapping_version=1.20.1
mod_id=dmzlegends
mod_name=DragonMineZ Legends
mod_license=MIT
mod_version=0.2.0
mod_group_id=dev.caiopacheco.dmzlegends
mod_authors=DMZ Legends
mod_description=Chefes especiais para DragonMine Z
""".strip())

    write("build.gradle", """
plugins {
    id 'eclipse'
    id 'idea'
    id 'maven-publish'
    id 'net.minecraftforge.gradle' version '[6.0,6.2)'
}

version = '0.2.0'
group = 'dev.caiopacheco.dmzlegends'

base {
    archivesName = 'dmzlegends'
}

java.toolchain.languageVersion = JavaLanguageVersion.of(17)

minecraft {
    mappings channel: 'official', version: '1.20.1'
    copyIdeResources = true

    runs {
        client {
            workingDirectory project.file('run')

            mods {
                dmzlegends {
                    source sourceSets.main
                }
            }
        }

        server {
            workingDirectory project.file('run-server')

            mods {
                dmzlegends {
                    source sourceSets.main
                }
            }
        }
    }
}

repositories {
    mavenCentral()
}

dependencies {
    minecraft 'net.minecraftforge:forge:1.20.1-47.4.10'
}

tasks.withType(JavaCompile).configureEach {
    options.encoding = 'UTF-8'
}
""".strip())

    write("src/main/resources/META-INF/mods.toml", """
modLoader="javafml"
loaderVersion="[47,)"
license="MIT"

[[mods]]
modId="dmzlegends"
version="0.2.0"
displayName="DragonMineZ Legends"
authors="DMZ Legends"
description='''Chefes e batalhas especiais para DragonMine Z.'''

[[dependencies.dmzlegends]]
modId="forge"
mandatory=true
versionRange="[47.4.10,)"
ordering="NONE"
side="BOTH"

[[dependencies.dmzlegends]]
modId="minecraft"
mandatory=true
versionRange="[1.20.1,1.20.2)"
ordering="NONE"
side="BOTH"

[[dependencies.dmzlegends]]
modId="dragonminez"
mandatory=false
versionRange="[2.2,)"
ordering="AFTER"
side="BOTH"
""".strip())

    write(
        "src/main/resources/pack.mcmeta",
        json.dumps({
            "pack": {
                "pack_format": 15,
                "description": "DragonMineZ Legends Assets"
            }
        }, indent=2)
    )


def create_registry():
    write(
        "src/main/java/dev/caiopacheco/dmzlegends/Legends.java",
        """
package dev.caiopacheco.dmzlegends;

import java.util.LinkedHashMap;
import java.util.Map;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Monster;

import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

@Mod(Legends.ID)
public class Legends {

    public static final String ID = "dmzlegends";

    public static final DeferredRegister<EntityType<?>> ENTITIES =
        DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, ID);

    public static final Map<String, RegistryObject<EntityType<LegendBoss>>>
        BOSSES = new LinkedHashMap<>();

    static {
        register("beerus");
        register("jiren");
        register("demigra");
    }

    private static void register(String name) {
        BOSSES.put(
            name,
            ENTITIES.register(name, () ->
                EntityType.Builder
                    .of(LegendBoss::new, MobCategory.MONSTER)
                    .sized(0.8F, 2.1F)
                    .clientTrackingRange(12)
                    .build(ID + ":" + name)
            )
        );
    }

    public Legends() {
        IEventBus bus =
            FMLJavaModLoadingContext.get().getModEventBus();

        ENTITIES.register(bus);
        bus.addListener(this::attributes);
    }

    private void attributes(EntityAttributeCreationEvent event) {
        for (var entry : BOSSES.entrySet()) {

            double health = switch (entry.getKey()) {
                case "beerus" -> 1500.0D;
                case "jiren" -> 2400.0D;
                case "demigra" -> 1900.0D;
                default -> 1000.0D;
            };

            event.put(
                entry.getValue().get(),
                Monster.createMonsterAttributes()
                    .add(Attributes.MAX_HEALTH, health)
                    .add(Attributes.ATTACK_DAMAGE, 22.0D)
                    .add(Attributes.ARMOR, 18.0D)
                    .add(Attributes.MOVEMENT_SPEED, 0.38D)
                    .add(Attributes.FOLLOW_RANGE, 48.0D)
                    .add(Attributes.KNOCKBACK_RESISTANCE, 0.9D)
                    .build()
            );
        }
    }
}
""".strip()
    )


def create_ai():
    write(
        "src/main/java/dev/caiopacheco/dmzlegends/LegendBoss.java",
        """
package dev.caiopacheco.dmzlegends;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;

import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;

import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;

import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;

import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import net.minecraftforge.registries.ForgeRegistries;

public class LegendBoss extends Monster {

    private static final EntityDataAccessor<Integer> PHASE =
        SynchedEntityData.defineId(
            LegendBoss.class,
            EntityDataSerializers.INT
        );

    private final ServerBossEvent bar = new ServerBossEvent(
        Component.translatable("entity.dmzlegends." + kind()),
        BossEvent.BossBarColor.PURPLE,
        BossEvent.BossBarOverlay.NOTCHED_10
    );

    private int cooldown = 100;
    private int casting = 0;

    public LegendBoss(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        xpReward = 1000;
    }

    public String kind() {
        var key = ForgeRegistries.ENTITY_TYPES.getKey(getType());
        return key == null ? "unknown" : key.getPath();
    }

    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        entityData.define(PHASE, 1);
    }

    public int phase() {
        return entityData.get(PHASE);
    }

    @Override
    protected void registerGoals() {
        goalSelector.addGoal(0, new FloatGoal(this));
        goalSelector.addGoal(
            1, new MeleeAttackGoal(this, 1.3D, true)
        );
        goalSelector.addGoal(
            5, new WaterAvoidingRandomStrollGoal(this, 0.8D)
        );
        goalSelector.addGoal(
            6, new LookAtPlayerGoal(this, Player.class, 16.0F)
        );
        goalSelector.addGoal(7, new RandomLookAroundGoal(this));

        targetSelector.addGoal(1, new HurtByTargetGoal(this));
        targetSelector.addGoal(
            2,
            new NearestAttackableTargetGoal<>(
                this, Player.class, true
            )
        );
    }

    @Override
    protected boolean removeWhenFarAway(double distance) {
        return false;
    }

    @Override
    public void startSeenByPlayer(ServerPlayer player) {
        super.startSeenByPlayer(player);
        bar.addPlayer(player);
    }

    @Override
    public void stopSeenByPlayer(ServerPlayer player) {
        super.stopSeenByPlayer(player);
        bar.removePlayer(player);
    }

    @Override
    public boolean hurt(DamageSource source, float damage) {
        float limit = Math.max(
            20.0F,
            getMaxHealth() * 0.09F
        );

        return super.hurt(source, Math.min(damage, limit));
    }

    @Override
    public void tick() {
        super.tick();

        if (!(level() instanceof ServerLevel server)) {
            return;
        }

        float health = Mth.clamp(
            getHealth() / getMaxHealth(),
            0.0F,
            1.0F
        );

        bar.setProgress(health);

        int currentPhase =
            health > 0.70F ? 1 :
            health > 0.40F ? 2 :
            health > 0.15F ? 3 : 4;

        if (currentPhase != phase()) {
            entityData.set(PHASE, currentPhase);

            server.sendParticles(
                ParticleTypes.EXPLOSION,
                getX(), getY() + 1.0D, getZ(),
                12, 1.0D, 1.0D, 1.0D, 0.1D
            );
        }

        if (tickCount % 8 == 0) {
            server.sendParticles(
                kind().equals("beerus")
                    ? ParticleTypes.DRAGON_BREATH
                    : kind().equals("jiren")
                        ? ParticleTypes.FLAME
                        : ParticleTypes.PORTAL,
                getX(), getY() + 1.1D, getZ(),
                5, 0.5D, 0.8D, 0.5D, 0.03D
            );
        }

        LivingEntity target = getTarget();

        if (target == null || !target.isAlive()) {
            casting = 0;
            return;
        }

        if (casting > 0) {
            casting--;

            if (casting == 0) {
                special(target);
            }

            return;
        }

        if (--cooldown > 0) {
            return;
        }

        if (distanceToSqr(target) <= 900.0D) {
            casting = 24;

            if (target instanceof ServerPlayer player) {
                player.displayClientMessage(
                    Component.literal(
                        "§c⚠ " + getName().getString()
                        + " está preparando um ataque!"
                    ),
                    true
                );
            }

            cooldown = Math.max(
                35,
                115 - phase() * 18
            );
        }
    }

    private float specialDamage(LivingEntity target) {
        return Mth.clamp(
            target.getMaxHealth() *
                (0.08F + phase() * 0.035F),
            8.0F,
            250.0F
        );
    }

    private void special(LivingEntity target) {
        switch (kind()) {

            case "beerus" -> {
                if (phase() >= 3) {
                    areaAttack(8.0D);
                } else {
                    beam(target);
                }

                if (phase() == 4) {
                    target.addEffect(
                        new MobEffectInstance(
                            MobEffects.WITHER, 80, 1
                        )
                    );
                }
            }

            case "jiren" -> {
                areaAttack(7.0D + phase());

                if (phase() >= 3) {
                    beam(target);
                }
            }

            case "demigra" -> {
                teleportBehind(target);

                target.addEffect(
                    new MobEffectInstance(
                        MobEffects.MOVEMENT_SLOWDOWN,
                        100, phase() >= 3 ? 2 : 1
                    )
                );

                target.addEffect(
                    new MobEffectInstance(
                        MobEffects.WEAKNESS,
                        100, 1
                    )
                );

                beam(target);

                if (phase() >= 3) {
                    heal(getMaxHealth() * 0.015F);
                }
            }

            default -> beam(target);
        }
    }

    private void beam(LivingEntity target) {
        if (!hasLineOfSight(target) ||
            distanceTo(target) > 30.0F) {
            return;
        }

        if (!(level() instanceof ServerLevel server)) {
            return;
        }

        Vec3 start = getEyePosition();
        Vec3 delta = target.getEyePosition().subtract(start);

        for (int i = 0; i <= 24; i++) {
            Vec3 pos = start.add(
                delta.scale(i / 24.0D)
            );

            server.sendParticles(
                ParticleTypes.END_ROD,
                pos.x, pos.y, pos.z,
                1, 0, 0, 0, 0
            );
        }

        target.hurt(
            damageSources().mobAttack(this),
            specialDamage(target)
        );
    }

    private void areaAttack(double radius) {
        if (!(level() instanceof ServerLevel server)) {
            return;
        }

        server.sendParticles(
            ParticleTypes.EXPLOSION,
            getX(), getY() + 1.0D, getZ(),
            14, radius * 0.4D, 1.0D,
            radius * 0.4D, 0
        );

        for (Player player : level().getEntitiesOfClass(
            Player.class,
            getBoundingBox().inflate(radius)
        )) {
            if (!player.isAlive()) {
                continue;
            }

            player.hurt(
                damageSources().mobAttack(this),
                specialDamage(player)
            );

            Vec3 direction = player.position()
                .subtract(position()).normalize();

            player.push(
                direction.x * 1.8D,
                0.5D,
                direction.z * 1.8D
            );
        }
    }

    private void teleportBehind(LivingEntity target) {
        Vec3 direction = target.getLookAngle();

        double x = target.getX() - direction.x * 2.5D;
        double y = target.getY();
        double z = target.getZ() - direction.z * 2.5D;

        BlockPos pos = BlockPos.containing(x, y, z);

        if (level().isEmptyBlock(pos) &&
            level().isEmptyBlock(pos.above())) {
            teleportTo(x, y, z);
        }
    }
}
""".strip()
    )


def create_renderer():
    write(
        "src/main/java/dev/caiopacheco/dmzlegends/ClientVisuals.java",
        """
package dev.caiopacheco.dmzlegends;

import java.util.HashMap;
import java.util.Map;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.ResourceLocation;

import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.EntityRenderersEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

@Mod.EventBusSubscriber(
    modid = Legends.ID,
    bus = Mod.EventBusSubscriber.Bus.MOD,
    value = Dist.CLIENT
)
public class ClientVisuals {

    public static final Map<String, ModelLayerLocation> LAYERS =
        new HashMap<>();

    static {
        for (String id : Legends.BOSSES.keySet()) {
            LAYERS.put(
                id,
                new ModelLayerLocation(
                    new ResourceLocation(Legends.ID, id),
                    "main"
                )
            );
        }
    }

    @SubscribeEvent
    public static void registerLayers(
        EntityRenderersEvent.RegisterLayerDefinitions event
    ) {
        for (String id : Legends.BOSSES.keySet()) {
            event.registerLayerDefinition(
                LAYERS.get(id),
                () -> createLayer(id)
            );
        }
    }

    @SubscribeEvent
    public static void registerRenderers(
        EntityRenderersEvent.RegisterRenderers event
    ) {
        for (var entry : Legends.BOSSES.entrySet()) {
            String id = entry.getKey();

            event.registerEntityRenderer(
                entry.getValue().get(),
                context -> new BossRenderer(context, id)
            );
        }
    }

    private static LayerDefinition createLayer(String id) {
        MeshDefinition mesh =
            HumanoidModel.createMesh(
                CubeDeformation.NONE, 0.0F
            );

        PartDefinition root = mesh.getRoot();
        PartDefinition head = root.getChild("head");

        if (id.equals("beerus")) {
            head.addOrReplaceChild(
                "divine_ears",
                CubeListBuilder.create()
                    .texOffs(0, 0)
                    .addBox(
                        -5.0F, -17.0F, -1.5F,
                        2.0F, 10.0F, 2.0F
                    )
                    .texOffs(0, 0)
                    .addBox(
                        3.0F, -17.0F, -1.5F,
                        2.0F, 10.0F, 2.0F
                    ),
                PartPose.ZERO
            );
        }

        if (id.equals("jiren")) {
            root.getChild("body").addOrReplaceChild(
                "power_armor",
                CubeListBuilder.create()
                    .texOffs(16, 16)
                    .addBox(
                        -5.0F, -1.0F, -2.5F,
                        10.0F, 5.0F, 5.0F
                    ),
                PartPose.ZERO
            );
        }

        if (id.equals("demigra")) {
            head.addOrReplaceChild(
                "demon_horns",
                CubeListBuilder.create()
                    .texOffs(0, 0)
                    .addBox(
                        -5.0F, -13.0F, -1.0F,
                        2.0F, 6.0F, 2.0F
                    )
                    .texOffs(0, 0)
                    .addBox(
                        3.0F, -13.0F, -1.0F,
                        2.0F, 6.0F, 2.0F
                    ),
                PartPose.ZERO
            );
        }

        return LayerDefinition.create(mesh, 64, 64);
    }

    private static class BossRenderer
        extends MobRenderer<LegendBoss, HumanoidModel<LegendBoss>> {

        private final String id;

        public BossRenderer(
            EntityRendererProvider.Context context,
            String id
        ) {
            super(
                context,
                new HumanoidModel<>(
                    context.bakeLayer(LAYERS.get(id))
                ),
                0.75F
            );

            this.id = id;
        }

        @Override
        public ResourceLocation getTextureLocation(
            LegendBoss boss
        ) {
            return new ResourceLocation(
                Legends.ID,
                "textures/entity/" + id + ".png"
            );
        }

        @Override
        protected void scale(
            LegendBoss boss,
            PoseStack pose,
            float partialTicks
        ) {
            float scale = switch (id) {
                case "beerus" -> 1.15F;
                case "jiren" -> 1.30F;
                case "demigra" -> 1.20F;
                default -> 1.0F;
            };

            pose.scale(scale, scale, scale);
        }
    }
}
""".strip()
    )


def create_textures():
    def rgb(value):
        return tuple(bytes.fromhex(value.lstrip("#"))) + (255,)

    def png_chunk(tag, content):
        data = tag + content
        return (
            struct.pack(">I", len(content))
            + data
            + struct.pack(">I", zlib.crc32(data) & 0xffffffff)
        )

    for name, profile in BOSSES.items():
        pixels = [
            [(0, 0, 0, 0) for _ in range(64)]
            for _ in range(64)
        ]

        skin = rgb(profile["skin"])
        outfit = rgb(profile["outfit"])
        accent = rgb(profile["accent"])
        eyes = rgb(profile["eyes"])

        def rect(x, y, w, h, color):
            for py in range(y, min(64, y + h)):
                for px in range(x, min(64, x + w)):
                    pixels[py][px] = color

        # Cubo da cabeça: frente, laterais, topo e costas.
        for x, y in [
            (8, 0), (16, 0),
            (0, 8), (8, 8), (16, 8), (24, 8)
        ]:
            rect(x, y, 8, 8, skin)

        # Corpo e uniforme.
        for x, y, w, h in [
            (20, 16, 8, 4),
            (16, 20, 4, 12),
            (20, 20, 8, 12),
            (28, 20, 4, 12),
            (32, 20, 8, 12)
        ]:
            rect(x, y, w, h, outfit)

        # Braços.
        for x, y in [(40, 20), (44, 20), (48, 20), (52, 20),
                     (32, 52), (36, 52), (40, 52), (44, 52)]:
            rect(x, y, 4, 12, outfit)

        # Pernas.
        for x, y in [(0, 20), (4, 20), (8, 20), (12, 20),
                     (16, 52), (20, 52), (24, 52), (28, 52)]:
            rect(x, y, 4, 12, outfit)

        # Olhos e detalhes identificadores.
        rect(10, 11, 2, 1, eyes)
        rect(14, 11, 2, 1, eyes)

        if name == "beerus":
            rect(20, 20, 8, 2, accent)
            rect(22, 23, 4, 6, accent)
            rect(20, 29, 8, 2, accent)

        elif name == "jiren":
            rect(20, 20, 8, 3, accent)
            rect(23, 23, 2, 7, accent)
            rect(10, 10, 2, 2, eyes)
            rect(14, 10, 2, 2, eyes)

        elif name == "demigra":
            rect(20, 20, 8, 2, accent)
            rect(23, 22, 2, 9, accent)
            rect(8, 8, 8, 2, rgb("#A12A48"))

        raw = bytearray()

        for row in pixels:
            raw.append(0)
            for pixel in row:
                raw.extend(pixel)

        header = struct.pack(
            ">IIBBBBB", 64, 64, 8, 6, 0, 0, 0
        )

        image = (
            b"\\x89PNG\\r\\n\\x1a\\n"
            + png_chunk(b"IHDR", header)
            + png_chunk(b"IDAT", zlib.compress(bytes(raw)))
            + png_chunk(b"IEND", b"")
        )

        path = (
            RES / "assets/dmzlegends/textures/entity"
            / f"{name}.png"
        )

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(image)


def create_languages():
    pt = {
        "itemGroup.dmzlegends": "DragonMineZ Legends"
    }

    en = {
        "itemGroup.dmzlegends": "DragonMineZ Legends"
    }

    for key, value in BOSSES.items():
        pt[f"entity.dmzlegends.{key}"] = value["name"]
        en[f"entity.dmzlegends.{key}"] = value["name"]

    write(
        "src/main/resources/assets/dmzlegends/lang/pt_br.json",
        json.dumps(pt, ensure_ascii=False, indent=2)
    )

    write(
        "src/main/resources/assets/dmzlegends/lang/en_us.json",
        json.dumps(en, ensure_ascii=False, indent=2)
    )


def build():
    print("\\nCompilando o addon...")

    log = ROOT / "compilacao.log"

    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            ["cmd", "/c", "gradlew.bat", "build", "--no-daemon"],
            cwd=ROOT,
            stdout=output,
            stderr=subprocess.STDOUT,
            check=False
        )

    if result.returncode != 0:
        print("[ERRO] A compilação não foi concluída.")
        print("Confira:", log)
        print("\\nÚltimas linhas do erro:")

        lines = log.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines()

        for line in lines[-35:]:
            print(line)

        return

    jars = [
        path for path in (ROOT / "build/libs").glob("*.jar")
        if not path.name.endswith("-sources.jar")
    ]

    if not jars:
        print("[ERRO] Nenhum JAR encontrado.")
        return

    jar = jars[0]

    required = [
        "dev/caiopacheco/dmzlegends/Legends.class",
        "dev/caiopacheco/dmzlegends/LegendBoss.class",
        "dev/caiopacheco/dmzlegends/ClientVisuals.class",
        "assets/dmzlegends/textures/entity/beerus.png",
        "assets/dmzlegends/textures/entity/jiren.png",
        "assets/dmzlegends/textures/entity/demigra.png",
        "META-INF/mods.toml"
    ]

    with zipfile.ZipFile(jar) as archive:
        files = set(archive.namelist())

    missing = [
        item for item in required if item not in files
    ]

    if missing:
        print("[ERRO] Arquivos ausentes no JAR:")
        for item in missing:
            print(item)
        return

    print("\\n[OK] JAR compilado e estrutura verificada!")
    print("Arquivo:", jar)


def main():
    print("===================================")
    print(" DragonMineZ Legends - Gerador")
    print("===================================")

    try:
        install_mdk()

        # Remove somente o código de exemplo do projeto MDK.
        source = ROOT / "src/main/java"
        if source.exists():
            shutil.rmtree(source)

        example = ROOT / "src/main/resources"
        if example.exists():
            shutil.rmtree(example)

        create_gradle()
        create_registry()
        create_ai()
        create_renderer()
        create_textures()
        create_languages()

        print("[OK] Projeto Java criado.")
        print("[OK] Entidades registradas.")
        print("[OK] Sistema de combate criado.")
        print("[OK] Renderizadores criados.")
        print("[OK] Texturas PNG geradas.")

        build()

    except Exception as error:
        print("\\n[ERRO]", type(error).__name__, error)
        sys.exit(1)


if __name__ == "__main__":
    main()