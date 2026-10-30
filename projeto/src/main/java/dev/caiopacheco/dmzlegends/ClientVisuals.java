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