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

        register("golden_frieza");
        register("hit");
        register("goku_black");
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

            double health = 1024.0D;

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