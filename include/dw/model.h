#ifndef DW_MODEL_H
#define DW_MODEL_H

#include <dw/types.h>
#include <dw/entity.h>

typedef struct {
	uint32_t useCount;
	void *modelPtr;
	int32_t *animTablePtr;
	void *mmdPtr;
	uint16_t pixelPage;
	uint16_t clutPage;
	uint8_t pixelOffsetX;
	uint8_t pixelOffsetY;
	int16_t modelId;
	int16_t digiType;
	uint16_t pad;
} ModelComponent;

int32_t getEntityType(Entity *entity);
ModelComponent *getEntityModelComponent(int32_t instance, int32_t type);

#endif /* DW_MODEL_H */
