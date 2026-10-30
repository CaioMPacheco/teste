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
    private boolean legendsHealthReady = false;

    public LegendBoss(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        xpReward = 1000;
    }

    public String kind() {
        var key = ForgeRegistries.ENTITY_TYPES.getKey(getType());
        return key == null ? "unknown" : key.getPath();
    }


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
    public boolean removeWhenFarAway(double distance) {
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
            getMaxHealth() * 0.06F
        );

        return super.hurt(source, Math.min(damage, limit));
    }

    @Override
    public void tick() {

        if (!level().isClientSide && !legendsHealthReady) {
            setHealth(getMaxHealth());
            legendsHealthReady = true;
        }

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
                        "Â§câš  " + getName().getString()
                        + " estÃ¡ preparando um ataque!"
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
                (0.07F + phase() * 0.035F),
            6.0F,
            1800000.0F
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

